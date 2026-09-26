"""My Diary service layer.

- Pure learner-owned data: nothing here reads or writes signals, evidence, the Passport or
  parent data, and nothing is sent to an AI provider.
- Progress rule (MVP): 1 saved entry = 1 page, toward a 100-page diary.
- Photos are validated with Pillow, auto-rotated, downscaled and re-encoded to WebP, which
  also strips EXIF/GPS metadata; anything that isn't a real JPEG/PNG/WebP image is rejected.
- Companion drafts are built deterministically from the student's own message — no AI call,
  nothing persisted until the student saves.
"""
from __future__ import annotations

import io
import re
from datetime import timedelta

from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.http import Http404
from django.utils import timezone
from PIL import Image, ImageOps, UnidentifiedImageError

from apps.companion.models import CompanionMessage, DiaryOffer, MessageRole

from .models import DiaryAttachment, DiaryEntry, EntrySource

PAGE_TARGET = 100
MAX_BODY_CHARS = 10_000
MAX_TAGS, MAX_TAG_CHARS = 8, 24
MAX_STICKERS = 6
STICKER_IDS = ("leaf", "flower", "star", "spark", "heart", "sun", "sprout", "note_grow")
MAX_PHOTOS = 4
MAX_PHOTO_BYTES = 5 * 1024 * 1024
MAX_PHOTO_SIDE = 1600
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
Image.MAX_IMAGE_PIXELS = 40_000_000  # refuse decompression bombs


class InvalidPhoto(ValueError):
    pass


# --- Field cleaning --------------------------------------------------------------


def clean_tags(tags) -> list[str]:
    seen, out = set(), []
    for tag in tags or []:
        text = " ".join(str(tag).split()).lstrip("#")[:MAX_TAG_CHARS]
        if text and text.lower() not in seen:
            seen.add(text.lower())
            out.append(text)
    return out[:MAX_TAGS]


def clean_stickers(stickers) -> list[dict]:
    """Known sticker IDs in fixed decorative slots only (no free-form canvas data)."""
    out, used = [], set()
    for item in stickers or []:
        if not isinstance(item, dict):
            continue
        sid, slot = item.get("id"), item.get("slot")
        if sid in STICKER_IDS and isinstance(slot, int) and 0 <= slot < MAX_STICKERS and slot not in used:
            used.add(slot)
            out.append({"id": sid, "slot": slot})
    return out


# --- Photos -----------------------------------------------------------------------


def process_photo(upload) -> tuple[ContentFile, int, int]:
    if upload.size > MAX_PHOTO_BYTES:
        raise InvalidPhoto("too_large")
    try:
        head = Image.open(upload)
        fmt = head.format
        head.verify()  # structural check without decoding everything
        upload.seek(0)
        image = Image.open(upload)
        image.load()
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise InvalidPhoto("not_an_image") from exc
    if fmt not in ALLOWED_FORMATS:
        raise InvalidPhoto("unsupported_type")

    image = ImageOps.exif_transpose(image)
    image = image.convert("RGBA" if image.mode in ("RGBA", "LA", "P") else "RGB")
    image.thumbnail((MAX_PHOTO_SIDE, MAX_PHOTO_SIDE), Image.LANCZOS)
    out = io.BytesIO()
    image.save(out, "WEBP", quality=82, method=4)  # new file: no EXIF / GPS carried over
    return ContentFile(out.getvalue()), image.width, image.height


@transaction.atomic
def add_photo(entry: DiaryEntry, upload, caption: str = "") -> DiaryAttachment:
    DiaryEntry.objects.select_for_update().only("id").get(pk=entry.pk)
    count = entry.attachments.count()
    if count >= MAX_PHOTOS:
        raise InvalidPhoto("too_many")
    content, width, height = process_photo(upload)
    attachment = DiaryAttachment(entry=entry, caption=caption[:120], order=count, width=width, height=height)
    attachment.image.save("photo.webp", content, save=False)
    attachment.save()
    DiaryEntry.objects.filter(pk=entry.pk).update(updated_at=timezone.now())
    return attachment


# --- Read models ------------------------------------------------------------------


def photo_payload(a: DiaryAttachment) -> dict:
    return {"id": a.id, "caption": a.caption, "width": a.width, "height": a.height}


def entry_summary(e: DiaryEntry, excerpt_chars: int = 160) -> dict:
    photos = list(e.attachments.all())
    body = " ".join(e.body.split())
    return {
        "id": e.id,
        "title": e.title,
        "excerpt": body[:excerpt_chars] + ("…" if len(body) > excerpt_chars else ""),
        "mood": e.mood or None,
        "entry_date": e.entry_date,
        "source": e.source,
        "tags": e.tags,
        "stickers": e.stickers,
        "cover_photo": photo_payload(photos[0]) if photos else None,
        "photo_count": len(photos),
        "updated_at": e.updated_at,
    }


def entry_detail(e: DiaryEntry) -> dict:
    return {
        **entry_summary(e),
        "body": e.body,
        "photos": [photo_payload(a) for a in e.attachments.all()],
        "created_at": e.created_at,
        "companion_message_id": e.companion_message_id,
    }


def overview(learner) -> dict:
    entries = DiaryEntry.objects.filter(learner=learner).prefetch_related("attachments")
    count = entries.count()
    today = timezone.localdate()
    monday = today - timedelta(days=today.weekday())
    week = {}
    for date, mood in (
        entries.filter(entry_date__gte=monday, entry_date__lte=monday + timedelta(days=6))
        .exclude(mood="")
        .order_by("entry_date", "created_at")
        .values_list("entry_date", "mood")
    ):
        week[date] = mood  # latest entry of the day wins
    recent = list(entries[:5])
    return {
        "pages_filled": count,
        "page_target": PAGE_TARGET,
        "photo_count": DiaryAttachment.objects.filter(entry__learner=learner).count(),
        "last_entry_at": recent[0].updated_at if recent else None,
        "recent_entries": [entry_summary(e) for e in recent],
        # The open book shows the three newest pages with a longer excerpt.
        "book_pages": [entry_summary(e, excerpt_chars=420) for e in recent[:3]],
        "mood_week": [
            {"date": monday + timedelta(days=i), "mood": week.get(monday + timedelta(days=i))} for i in range(7)
        ],
        "pending_moment": pending_moment(learner),
    }


def pending_moment(learner) -> dict | None:
    """The newest Companion offer the student hasn't saved or dismissed (their own words only)."""
    offer = (
        CompanionMessage.objects.filter(
            role=MessageRole.ASSISTANT,
            conversation__learner=learner,
            diary_offer=DiaryOffer.OFFERED,
            reply_to__diary_entry__isnull=True,
        )
        .select_related("reply_to")
        .order_by("-created_at", "-id")
        .first()
    )
    if offer is None or offer.reply_to is None:
        return None
    text = " ".join(offer.reply_to.content.split())
    return {
        "assistant_message_id": offer.id,
        "student_message_id": offer.reply_to_id,
        "excerpt": text[:140] + ("…" if len(text) > 140 else ""),
        "created_at": offer.created_at,
    }


# --- Companion → Diary ---------------------------------------------------------------

_SENTENCE = re.compile(r"(?<=[.!?…])\s+")


def _draft_title(text: str) -> str:
    first = _SENTENCE.split(" ".join(text.split()), maxsplit=1)[0].rstrip(".!?… ")
    return first if len(first) <= 70 else first[:69].rsplit(" ", 1)[0] + "…"


def owned_student_message(learner, message_id: int) -> CompanionMessage:
    """The student's own Companion message (never the assistant's, never another learner's)."""
    msg = (
        CompanionMessage.objects.filter(pk=message_id, role=MessageRole.USER, conversation__learner=learner)
        .select_related("diary_entry")
        .first()
    )
    if msg is None:
        raise Http404
    return msg


def _existing_entry_id(msg: CompanionMessage):
    try:
        return msg.diary_entry.id
    except DiaryEntry.DoesNotExist:
        return None


def companion_draft(learner, message_id: int) -> dict:
    """Prefill for the editor, built only from the student's own words. Nothing is stored.
    If this message was already saved, the existing entry id is returned instead."""
    msg = owned_student_message(learner, message_id)
    existing = _existing_entry_id(msg)
    if existing:
        return {"existing_entry_id": existing}
    return {
        "existing_entry_id": None,
        "draft": {
            "title": _draft_title(msg.content),
            "body": msg.content,
            "entry_date": timezone.localtime(msg.created_at).date(),
            "source": EntrySource.COMPANION,
            "companion_message_id": msg.id,
        },
    }


def create_entry(learner, data: dict) -> tuple[DiaryEntry, bool]:
    """Create an entry. With `companion_message_id` (explicit "Add to My Diary" + Save), at most
    one entry per message: a repeated save returns the existing entry (created=False)."""
    message_id = data.pop("companion_message_id", None)
    msg = owned_student_message(learner, message_id) if message_id else None
    if msg is not None:
        existing = _existing_entry_id(msg)
        if existing:
            return DiaryEntry.objects.get(pk=existing), False
    try:
        with transaction.atomic():
            entry = DiaryEntry.objects.create(
                learner=learner,
                source=EntrySource.COMPANION if msg else EntrySource.MANUAL,
                companion_message=msg,
                **data,
            )
    except IntegrityError:  # the same message saved concurrently
        return DiaryEntry.objects.get(companion_message=msg, learner=learner), False
    return entry, True


"""Resources, learning paths and opportunities: read models + learner interaction state.

The catalog is small (tens of rows), so filtering/search runs on localized values in Python —
it works the same in EN/UZ/RU without full-text machinery.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from common.i18n import tr

from apps.evidence.models import Evidence, EvidenceKind, EvidenceSource
from apps.evidence.services import Contribution, record_evidence

from ..models import (
    LearnerOpportunity,
    LearnerResource,
    LearningPath,
    Opportunity,
    Organization,
    ProgressStatus,
    Resource,
    ResourceType,
)
from .matching import Profile, eligibility, learner_profile, match_item, rank_key

RESOURCE_EVIDENCE_WEIGHT = Decimal("0.30")  # finishing a resource is light exposure evidence


class ActionError(Exception):
    pass


def _iso(d) -> str | None:
    return d.isoformat() if d else None


def organization_summary(org: Organization) -> dict:
    return {
        "slug": org.slug,
        "name": tr(org, "name"),
        "type": org.organization_type,
        "short_description": tr(org, "short_description"),
        "website_url": org.website_url,
        "city": tr(org, "city"),
        "country": tr(org, "country"),
        "verified": org.verified,
        "is_demo": org.is_demo,
    }


def _matches_query(q: str, *values) -> bool:
    q = q.strip().lower()
    return not q or any(q in (v or "").lower() for v in values)


# --- Resources ------------------------------------------------------------------------------


def _resource_states(learner, resources) -> dict[int, LearnerResource]:
    return {s.resource_id: s for s in LearnerResource.objects.filter(learner=learner, resource__in=resources)}


def resource_card(r: Resource, state: LearnerResource | None, match: dict) -> dict:
    return {
        "slug": r.slug,
        "title": tr(r, "title"),
        "short_description": tr(r, "short_description"),
        "type": r.resource_type,
        "category": r.category,
        "cover_key": r.cover_key,
        "duration_minutes": r.duration_minutes,
        "difficulty": r.difficulty,
        "is_external": bool(r.external_url),
        "organization": organization_summary(r.organization),
        "featured": r.featured,
        "saved": bool(state and state.saved),
        "status": state.status if state else ProgressStatus.NOT_STARTED,
        "match": match,
    }


def _active_resources():
    return Resource.objects.filter(active=True, organization__active=True).select_related("organization")


def path_summary(path: LearningPath, learner, profile: Profile, *, with_items: bool = False) -> dict:
    items = [i.resource for i in path.items.select_related("resource__organization") if i.resource.active]
    states = _resource_states(learner, items)
    out = {
        "slug": path.slug,
        "title": tr(path, "title"),
        "description": tr(path, "description"),
        "category": path.category,
        "cover_key": path.cover_key,
        "difficulty": path.difficulty,
        "organization": organization_summary(path.organization),
        "resource_count": len(items),
        "duration_minutes": sum(r.duration_minutes for r in items),
        "completed_count": sum(1 for r in items if states.get(r.id) and states[r.id].status == ProgressStatus.COMPLETED),
        "next_resource": next(
            (r.slug for r in items if not (states.get(r.id) and states[r.id].status == ProgressStatus.COMPLETED)), None
        ),
    }
    if with_items:
        out["items"] = [resource_card(r, states.get(r.id), match_item(profile, r)) for r in items]
    return out


def featured_path() -> LearningPath | None:
    return LearningPath.objects.filter(active=True, featured=True, organization__active=True).select_related("organization").first()


SORTS = ("relevant", "shortest", "newest")


def resource_list(learner, *, rtype=None, category=None, q="", saved=False, sort="relevant") -> dict:
    profile = learner_profile(learner)
    resources = list(_active_resources())
    states = _resource_states(learner, resources)
    rows = []
    for r in resources:
        if rtype and r.resource_type != rtype:
            continue
        if category and r.category != category:
            continue
        if saved and not (states.get(r.id) and states[r.id].saved):
            continue
        if not _matches_query(q, tr(r, "title"), tr(r, "short_description"), tr(r.organization, "name")):
            continue
        rows.append((r, match_item(profile, r)))
    if sort == "shortest":
        rows.sort(key=lambda rm: (rm[0].duration_minutes, rm[0].id))
    elif sort == "newest":
        rows.sort(key=lambda rm: (-rm[0].created_at.timestamp(), -rm[0].id))
    else:
        rows.sort(key=lambda rm: rank_key(rm[1], rm[0]))
    path = featured_path()
    return {
        "has_signals": profile.has_signals,
        "featured_path": path_summary(path, learner, profile) if path else None,
        "items": [resource_card(r, states.get(r.id), m) for r, m in rows],
    }


def get_resource(slug: str) -> Resource:
    return _active_resources().get(slug=slug)


def resource_detail(learner, r: Resource) -> dict:
    profile = learner_profile(learner)
    state = LearnerResource.objects.filter(learner=learner, resource=r).first()
    paths = LearningPath.objects.filter(active=True, items__resource=r).distinct()
    return {
        **resource_card(r, state, match_item(profile, r)),
        "content": tr(r, "content") or {},
        "external_url": r.external_url,
        "produces_evidence": r.produces_evidence and bool(r.evidence_signals),
        "evidence_recorded": bool(
            state and Evidence.objects.filter(source_type=EvidenceSource.RESOURCE, source_id=state.id).exists()
        ),
        "tracks_progress": r.resource_type == ResourceType.COURSE,
        "paths": [{"slug": p.slug, "title": tr(p, "title")} for p in paths],
        "has_signals": profile.has_signals,
    }


RESOURCE_ACTIONS = ("save", "unsave", "open", "start", "complete", "reset")


@transaction.atomic
def resource_action(learner, r: Resource, action: str) -> LearnerResource:
    """save/unsave · open (first open of a course starts it) · start (courses) · complete · reset."""
    state, _ = LearnerResource.objects.select_for_update().get_or_create(learner=learner, resource=r)
    now = timezone.now()
    if action in ("save", "unsave"):
        state.saved = action == "save"
    elif action == "open":
        state.opened_at = state.opened_at or now
        if r.resource_type == ResourceType.COURSE and state.status == ProgressStatus.NOT_STARTED:
            state.status = ProgressStatus.IN_PROGRESS
    elif action == "start":
        if r.resource_type != ResourceType.COURSE:
            raise ActionError("Only courses have an in-progress state.")
        if state.status == ProgressStatus.NOT_STARTED:
            state.status = ProgressStatus.IN_PROGRESS
    elif action == "complete":
        state.opened_at = state.opened_at or now
        if state.status != ProgressStatus.COMPLETED:
            state.status, state.completed_at = ProgressStatus.COMPLETED, now
    elif action == "reset":
        # Undo a mistaken "complete". Evidence already recorded stays (evidence is append-only).
        state.status, state.completed_at = ProgressStatus.NOT_STARTED, None
    else:
        raise ActionError("Unknown action.")
    state.save()
    if action == "complete":
        _record_resource_evidence(learner, r, state)
    return state


def _record_resource_evidence(learner, r: Resource, state: LearnerResource) -> None:
    """Only resources explicitly configured for it produce evidence: EXPOSURE, light weight,
    once per learner+resource (evidence is idempotent per source id)."""
    if not (r.produces_evidence and r.evidence_signals):
        return
    from apps.passports.services import sync_passport  # avoid import cycle

    record_evidence(
        learner=learner,
        source_type=EvidenceSource.RESOURCE,
        source_id=state.id,
        title=r.title,
        description=f"Completed the {r.get_resource_type_display().lower()} “{r.title}”.",
        contributions=[
            Contribution(k, EvidenceKind.EXPOSURE, RESOURCE_EVIDENCE_WEIGHT, observation=f"completed resource {r.slug}")
            for k in r.evidence_signals
        ],
        metadata={"resource": r.slug, "type": r.resource_type},
    )
    sync_passport(learner)


def path_detail(learner, path: LearningPath) -> dict:
    return path_summary(path, learner, learner_profile(learner), with_items=True)


# --- Opportunities --------------------------------------------------------------------------


def _active_opportunities():
    return Opportunity.objects.filter(active=True, organization__active=True).select_related("organization")


def opportunity_card(o: Opportunity, state: LearnerOpportunity | None, match: dict, today: date) -> dict:
    return {
        "slug": o.slug,
        "title": tr(o, "title"),
        "short_description": tr(o, "short_description"),
        "type": o.opportunity_type,
        "category": o.category,
        "mode": o.mode,
        "city": tr(o, "city"),
        "country": tr(o, "country"),
        "global_available": o.global_available,
        "age_min": o.age_min,
        "age_max": o.age_max,
        "application_deadline": _iso(o.application_deadline),
        "program_start": _iso(o.program_start),
        "program_end": _iso(o.program_end),
        "cover_key": o.cover_key,
        "organization": organization_summary(o.organization),
        "featured": o.featured,
        "saved": bool(state and state.saved),
        "state": state.state if state else "NONE",
        "match": match,
        "eligibility": eligibility(o, today),
    }


def _fits_age(o: Opportunity, age: int | None) -> bool:
    return age is None or ((o.age_min or 0) <= age <= (o.age_max or 99))


def opportunity_list(
    learner, *, category=None, mode=None, otype=None, country=None, age=None, deadline=None, q="", saved=False,
    today: date | None = None,
) -> dict:
    from apps.engagement.services import local_day

    today = today or local_day()
    profile = learner_profile(learner)
    opps = list(_active_opportunities())
    states = {s.opportunity_id: s for s in LearnerOpportunity.objects.filter(learner=learner, opportunity__in=opps)}
    rows = []
    for o in opps:
        elig = eligibility(o, today)
        status = elig["deadline"]["status"]
        if deadline == "closing_soon" and status != "CLOSING_SOON":
            continue
        if deadline != "all" and status == "CLOSED" and not saved:
            continue
        if category and o.category != category:
            continue
        if mode == "ONLINE" and o.mode != "ONLINE":
            continue
        if mode == "IN_PERSON" and o.mode not in ("IN_PERSON", "HYBRID"):
            continue
        if otype and o.opportunity_type != otype:
            continue
        if country and o.country != country and not o.global_available:
            continue
        if not _fits_age(o, age):
            continue
        if saved and not (states.get(o.id) and states[o.id].saved):
            continue
        if not _matches_query(q, tr(o, "title"), tr(o, "short_description"), tr(o.organization, "name")):
            continue
        rows.append((o, match_item(profile, o), elig))
    rows.sort(key=lambda row: (row[2]["deadline"]["status"] == "CLOSED",) + rank_key(row[1], row[0]))
    cards = [opportunity_card(o, states.get(o.id), m, today) for o, m, _ in rows]
    open_cards = [c for c in cards if c["eligibility"]["open_now"]]
    featured = None
    if profile.has_signals:
        featured = next((c for c in open_cards if c["match"]["level"] == "STRONG_FIT"), None)
    featured = featured or next((c for c in open_cards if c["featured"]), None)
    return {
        "has_signals": profile.has_signals,
        "featured": featured,
        "items": cards,
        "facets": {
            "countries": sorted({o.country for o in opps if o.country}),
            "types": sorted({o.opportunity_type for o in opps}),
        },
    }


def get_opportunity(slug: str) -> Opportunity:
    return _active_opportunities().get(slug=slug)


def opportunity_detail(learner, o: Opportunity, today: date | None = None) -> dict:
    from apps.engagement.services import local_day

    today = today or local_day()
    profile = learner_profile(learner)
    state = LearnerOpportunity.objects.filter(learner=learner, opportunity=o).first()
    return {
        **opportunity_card(o, state, match_item(profile, o), today),
        "description": tr(o, "description"),
        "skills": tr(o, "skills") or [],
        "requirements": tr(o, "eligibility") or [],
        "faqs": tr(o, "faqs") or [],
        "application_url": o.application_url,
        "application_open_at": _iso(o.application_open_at),
        "has_signals": profile.has_signals,
    }


OPPORTUNITY_ACTIONS = ("save", "unsave", "view", "open_link")


@transaction.atomic
def opportunity_action(learner, o: Opportunity, action: str) -> LearnerOpportunity:
    if action not in OPPORTUNITY_ACTIONS:
        raise ActionError("Unknown action.")
    state, _ = LearnerOpportunity.objects.select_for_update().get_or_create(learner=learner, opportunity=o)
    now = timezone.now()
    if action in ("save", "unsave"):
        state.saved = action == "save"
    elif action == "view":
        state.viewed_at = state.viewed_at or now
    else:  # open_link: the learner opened the provider's page. Not an application.
        state.viewed_at = state.viewed_at or now
        state.link_opened_at = state.link_opened_at or now
    state.save()
    return state

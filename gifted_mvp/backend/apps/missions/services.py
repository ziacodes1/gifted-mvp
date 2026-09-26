"""Mission logic: response validation, deterministic evidence, completion, matching.

No LLM is used here. Mission completion creates evidence through the generic
`apps.evidence.services.record_evidence`, exactly as a future virtual lab would.
"""
from __future__ import annotations

import re
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.evidence.models import EvidenceSource
from apps.evidence.services import Contribution, record_evidence

from .models import AttemptStatus, Mission, MissionAttempt, MissionStep, StepType

# --- Response validation ------------------------------------------------------


def _option_keys(step: MissionStep) -> set[str]:
    return {o["key"] for o in step.content.get("options", [])}


def _selected_list(data) -> list[str]:
    selected = data.get("selected") if isinstance(data, dict) else None
    if not isinstance(selected, list) or not all(isinstance(k, str) for k in selected):
        raise ValidationError("`selected` must be a list of option keys.")
    return list(dict.fromkeys(selected))  # dedupe, keep order


def validate_response(step: MissionStep, data) -> dict:
    """Return cleaned response data or raise ValidationError. Rules live in step.content."""
    c = step.content
    if step.type == StepType.CONTEXT:
        return {"acknowledged": True}

    if step.type == StepType.MULTI_SELECT:
        selected = _selected_list(data)
        if not set(selected) <= _option_keys(step):
            raise ValidationError("Unknown option.")
        lo, hi = c.get("min", 1), c.get("max", len(selected))
        if not lo <= len(selected) <= hi:
            raise ValidationError(f"Choose between {lo} and {hi} options.")
        return {"selected": selected}

    if step.type == StepType.BUDGET:
        selected = _selected_list(data)
        costs = {o["key"]: o["cost"] for o in c.get("options", [])}
        if not set(selected) <= set(costs):
            raise ValidationError("Unknown option.")
        if len(selected) < c.get("min_items", 1):
            raise ValidationError("Choose at least one improvement.")
        spent = sum(costs[k] for k in selected)
        if spent > c["budget"]:
            raise ValidationError(f"That costs {spent} points — your budget is {c['budget']}.")
        return {"selected": selected, "spent": spent}

    if step.type == StepType.SINGLE_CHOICE:
        selected = data.get("selected") if isinstance(data, dict) else None
        if selected not in _option_keys(step):
            raise ValidationError("Choose one option.")
        return {"selected": selected}

    if step.type == StepType.REFLECTION:
        if not isinstance(data, dict):
            raise ValidationError("Invalid reflection.")
        cleaned = {}
        for f in c.get("fields", []):
            value = data.get(f["key"], "")
            value = re.sub(r"\s+", " ", value if isinstance(value, str) else "").strip()
            if f.get("required") and len(value) < f.get("min_length", 1):
                raise ValidationError(f"{f['label']}: please write at least {f.get('min_length', 1)} characters.")
            if len(value) > f.get("max_length", 600):
                raise ValidationError(f"{f['label']}: please keep it under {f['max_length']} characters.")
            cleaned[f["key"]] = value
        return cleaned

    raise ValidationError("Unsupported step type.")


# --- Attempt lifecycle ----------------------------------------------------------


def start_attempt(learner, mission: Mission) -> tuple[MissionAttempt, bool]:
    """Resume the learner's attempt (in progress or completed) or create one."""
    attempt, created = MissionAttempt.objects.get_or_create(
        learner=learner, mission=mission, defaults={"status": AttemptStatus.IN_PROGRESS}
    )
    return attempt, created


def save_response(attempt: MissionAttempt, step: MissionStep, data) -> None:
    if attempt.status == AttemptStatus.COMPLETED:
        raise ValidationError("This mission is already completed.")
    if step.mission_id != attempt.mission_id:
        raise ValidationError("Step does not belong to this mission.")
    attempt.responses.update_or_create(step=step, defaults={"data": validate_response(step, data)})


def missing_steps(attempt: MissionAttempt) -> list[MissionStep]:
    answered = set(attempt.responses.values_list("step_id", flat=True))
    return [s for s in attempt.mission.steps.all() if s.id not in answered]


def _chosen(step: MissionStep, data: dict, option_key: str) -> bool:
    if step.type == StepType.REFLECTION:
        return bool(data.get(option_key))
    selected = data.get("selected")
    return option_key in selected if isinstance(selected, list) else option_key == selected


def compute_contributions(attempt: MissionAttempt) -> list[Contribution]:
    responses = {r.step_id: r.data for r in attempt.responses.all()}
    out: list[Contribution] = []
    for m in attempt.mission.signal_maps.select_related("signal", "step"):
        if m.step_id is None:
            applies = True
        elif m.step_id not in responses:
            applies = False
        elif not m.option_key:
            applies = True
        else:
            applies = _chosen(m.step, responses[m.step_id], m.option_key)
        if applies:
            out.append(Contribution(m.signal.key, m.kind, Decimal(m.weight), m.observation))
    return out


def _observed_choices(attempt: MissionAttempt) -> dict:
    """Plain record of what the learner chose (labels, not hidden mappings)."""
    out = {}
    for r in attempt.responses.select_related("step"):
        step = r.step
        if step.type == StepType.CONTEXT:
            continue
        labels = {o["key"]: o["label"] for o in step.content.get("options", [])}
        if step.type == StepType.REFLECTION:
            out[step.key] = r.data
        elif isinstance(r.data.get("selected"), list):
            out[step.key] = [labels.get(k, k) for k in r.data["selected"]]
        else:
            out[step.key] = labels.get(r.data.get("selected"), r.data.get("selected"))
    return out


def complete_attempt(attempt: MissionAttempt):
    """Idempotent. Locks the attempt, creates Evidence once, syncs the Passport.
    Returns (evidence, created)."""
    from apps.passports.services import sync_passport  # avoid import cycle

    with transaction.atomic():
        attempt = MissionAttempt.objects.select_for_update().select_related("mission").get(pk=attempt.pk)
        if attempt.status != AttemptStatus.COMPLETED:
            missing = missing_steps(attempt)
            if missing:
                raise ValidationError(f"Finish every step before completing ({len(missing)} left).")
        evidence, created = record_evidence(
            learner=attempt.learner,
            source_type=EvidenceSource.MISSION,
            source_id=attempt.id,
            title=attempt.mission.title,
            description=attempt.mission.short_description,
            contributions=compute_contributions(attempt),
            metadata={"mission": attempt.mission.slug, "choices": _observed_choices(attempt)},
        )
        if attempt.status != AttemptStatus.COMPLETED:
            attempt.status = AttemptStatus.COMPLETED
            attempt.completed_at = timezone.now()
            attempt.save(update_fields=["status", "completed_at"])
    sync_passport(attempt.learner)
    from apps.engagement.rules import EventType
    from apps.engagement.services import safe_record

    safe_record(attempt.learner, EventType.MISSION_COMPLETED, f"attempt:{attempt.id}", attempt.completed_at)
    return evidence, created


# --- Recommendation -------------------------------------------------------------


def match_mission(next_step: dict | None, mission: Mission) -> str:
    """RECOMMENDED if the saved next-step recommendation loosely points at what
    this mission explores; otherwise SUGGESTED. Honest, deterministic, cheap."""
    if not next_step:
        return "SUGGESTED"
    keys = {s if isinstance(s, str) else s.get("key") for s in next_step.get("signals_used", [])}
    if keys & set(mission.metadata.get("match_signals", [])):
        return "RECOMMENDED"
    text = " ".join(
        str(next_step.get(k, "")) for k in ("title", "activity_type", "reason", "intended_validation")
    ).lower()
    words = mission.metadata.get("match_keywords", [])
    return "RECOMMENDED" if any(re.search(rf"\b{re.escape(w)}", text) for w in words) else "SUGGESTED"


def featured_mission() -> Mission | None:
    return Mission.objects.filter(is_active=True).order_by("order", "id").first()

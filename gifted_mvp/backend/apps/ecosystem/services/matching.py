"""Deterministic Passport → catalog matching. No scores are shown, no AI is called.

Inputs are the learner's *deterministic* signals (`LearnerSignal`, from assessment scoring)
and which signals their non-assessment evidence (missions, resources) touched. Nothing
private — diary, Companion, reflections, raw answers — is read here.

Output per item:
    {"level": STRONG_FIT | WORTH_EXPLORING | NEW_AREA | EXPLORE, "reasons": [...]}
Reasons are codes + a localized signal label; the frontend turns them into sentences, so
every "why" shown to the learner is traceable to a specific signal.

    STRONG_FIT       ≥2 clear matches, or 1 clear match that missions/resources also showed
    WORTH_EXPLORING  1 clear or emerging match, or a first-hand experience the learner lacks
    NEW_AREA         nothing in the Passport points here yet — offered as something to try
    EXPLORE          no assessment yet: the learner sees suggestions, not matches
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from common.i18n import tr

from apps.evidence.models import EvidenceSource, SignalEvidence
from apps.signals.models import LearnerSignal, SignalCategory

CLEAR = 60  # score at/above which a signal counts as a clear match
EMERGING = 40  # emerging interest
LOW_EXPOSURE = 40  # exposure below this = the learner hasn't done much of it yet
CLOSING_SOON_DAYS = 14
MAX_REASONS = 4

STRONG_FIT, WORTH_EXPLORING, NEW_AREA, EXPLORE = "STRONG_FIT", "WORTH_EXPLORING", "NEW_AREA", "EXPLORE"
LEVEL_RANK = {STRONG_FIT: 0, WORTH_EXPLORING: 1, NEW_AREA: 2, EXPLORE: 3}

_REASON_BY_CATEGORY = {
    SignalCategory.INTEREST: "interest",
    SignalCategory.WORK_STYLE: "work_style",
    SignalCategory.VALUE: "value",
    SignalCategory.APTITUDE: "aptitude",
}


@dataclass
class Profile:
    """What matching may know about a learner (built once per request)."""

    scores: dict[str, int] = field(default_factory=dict)
    categories: dict[str, str] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    evidence_keys: set[str] = field(default_factory=set)

    @property
    def has_signals(self) -> bool:
        return bool(self.scores)

    def top_interests(self, minimum: int = EMERGING) -> list[str]:
        keys = [k for k, c in self.categories.items() if c == SignalCategory.INTEREST and self.scores[k] >= minimum]
        return sorted(keys, key=lambda k: (-self.scores[k], k))


def learner_profile(learner) -> Profile:
    profile = Profile()
    for ls in LearnerSignal.objects.filter(learner=learner, signal__is_active=True).select_related("signal"):
        key = ls.signal.key
        profile.scores[key] = ls.score
        profile.categories[key] = ls.signal.category
        profile.labels[key] = tr(ls.signal, "label")
    profile.evidence_keys = set(
        SignalEvidence.objects.filter(evidence__learner=learner)
        .exclude(evidence__source_type=EvidenceSource.ASSESSMENT)
        .values_list("signal__key", flat=True)
    )
    return profile


def match_item(profile: Profile, item) -> dict:
    """Match any `Matchable` (resource / opportunity) — or anything with `target_signals`
    and `target_exposure` lists — against a profile."""
    if not profile.has_signals:
        return {"level": EXPLORE, "reasons": []}

    targets = [k for k in (item.target_signals or []) if k in profile.scores]
    clear = sorted((k for k in targets if profile.scores[k] >= CLEAR), key=lambda k: (-profile.scores[k], k))
    emerging = sorted(
        (k for k in targets if EMERGING <= profile.scores[k] < CLEAR), key=lambda k: (-profile.scores[k], k)
    )
    backed = [k for k in clear + emerging if k in profile.evidence_keys]
    gaps = [
        k for k in (getattr(item, "target_exposure", None) or [])
        if k in profile.scores and profile.scores[k] < LOW_EXPOSURE
    ]

    def reason(code: str, key: str) -> dict:
        return {"code": code, "signal": key, "label": profile.labels.get(key, key)}

    reasons = [reason(_REASON_BY_CATEGORY.get(profile.categories[k], "interest"), k) for k in clear]
    reasons += [reason("evidence", k) for k in backed[:1]]
    reasons += [reason("exposure_gap", k) for k in gaps[:1]]
    reasons += [reason("emerging", k) for k in emerging]

    if len(clear) >= 2 or (clear and backed):
        level = STRONG_FIT
    elif clear or emerging or gaps:
        level = WORTH_EXPLORING
    else:
        level = NEW_AREA
        reasons = [{"code": "new_area", "signal": None, "label": ""}]
    return {"level": level, "reasons": reasons[:MAX_REASONS]}


def rank_key(match: dict, item) -> tuple:
    """Sort key: better level first, more reasons, featured, then admin order."""
    return (
        LEVEL_RANK[match["level"]],
        -len([r for r in match["reasons"] if r["code"] != "new_area"]),
        not getattr(item, "featured", False),
        getattr(item, "order", 0),
        item.id,
    )


# --- Opportunity eligibility ---------------------------------------------------------------


def deadline_status(opportunity, today: date) -> dict:
    opens, deadline = opportunity.application_open_at, opportunity.application_deadline
    if opens and opens > today:
        return {"status": "NOT_YET_OPEN", "days_left": None, "opens": opens.isoformat()}
    if deadline is None:
        return {"status": "ROLLING", "days_left": None}
    days = (deadline - today).days
    if days < 0:
        return {"status": "CLOSED", "days_left": None}
    return {"status": "CLOSING_SOON" if days <= CLOSING_SOON_DAYS else "OPEN", "days_left": days}


def eligibility(opportunity, today: date) -> dict:
    """What we can state honestly. Gifted doesn't store a learner's age or city, so age and
    location are shown as requirements to check, never as a pass/fail verdict."""
    if opportunity.global_available:
        where = "ANYWHERE"
    elif opportunity.mode == "ONLINE":
        where = "ONLINE_REGION"  # online, but for learners in `country`
    else:
        where = "ON_SITE"
    deadline = deadline_status(opportunity, today)
    return {
        "age": {
            "min": opportunity.age_min,
            "max": opportunity.age_max,
            "status": "CHECK" if (opportunity.age_min or opportunity.age_max) else "ANY",
        },
        "location": {
            "status": where,
            "mode": opportunity.mode,
            "city": opportunity.city,
            "country": opportunity.country,
        },
        "deadline": deadline,
        "open_now": deadline["status"] in ("OPEN", "CLOSING_SOON", "ROLLING"),
    }


def match_opportunity(learner, opportunity, *, profile: Profile | None = None, today: date | None = None) -> dict:
    """{match_level, reasons, eligibility} — no percentages, every reason traceable."""
    from apps.engagement.services import local_day

    profile = profile if profile is not None else learner_profile(learner)
    match = match_item(profile, opportunity)
    return {
        "match_level": match["level"],
        "reasons": match["reasons"],
        "eligibility": eligibility(opportunity, today or local_day()),
    }

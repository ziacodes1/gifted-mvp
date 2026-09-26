"""Ecosystem services. `for_you` feeds the small Home / Passport "Explore next" cards."""
from __future__ import annotations

from apps.engagement.services import local_day

from ..models import CommunityMembership, LearnerOpportunity, LearnerResource, ProgressStatus
from . import catalog, community
from .matching import (  # noqa: F401  (public API)
    learner_profile,
    match_item,
    match_opportunity,
    rank_key,
)


def for_you(learner) -> dict:
    """One resource, one open opportunity and one circle — the best deterministic match the
    learner hasn't already finished / opened / joined. Without signals: featured picks."""
    today = local_day()
    profile = learner_profile(learner)

    done = set(
        LearnerResource.objects.filter(learner=learner, status=ProgressStatus.COMPLETED).values_list("resource_id", flat=True)
    )
    resources = [r for r in catalog._active_resources() if r.id not in done]
    scored = sorted(((match_item(profile, r), r) for r in resources), key=lambda mr: rank_key(mr[0], mr[1]))
    resource = None
    if scored:
        match, r = scored[0]
        state = LearnerResource.objects.filter(learner=learner, resource=r).first()
        resource = catalog.resource_card(r, state, match)

    opened = set(
        LearnerOpportunity.objects.filter(learner=learner, link_opened_at__isnull=False).values_list("opportunity_id", flat=True)
    )
    opps = [
        o for o in catalog._active_opportunities()
        if o.id not in opened and catalog.eligibility(o, today)["open_now"]
    ]
    ranked = sorted(((match_item(profile, o), o) for o in opps), key=lambda mo: rank_key(mo[0], mo[1]))
    opportunity = None
    if ranked:
        match, o = ranked[0]
        state = LearnerOpportunity.objects.filter(learner=learner, opportunity=o).first()
        opportunity = catalog.opportunity_card(o, state, match, today)

    joined = set(CommunityMembership.objects.filter(learner=learner).values_list("circle_id", flat=True))
    circles = list(community._circles())
    picks = community.suggest_circles(profile, circles, joined)
    circle = community.circle_card(picks[0][0], joined, picks[0][1]) if picks else None

    return {"has_signals": profile.has_signals, "resource": resource, "opportunity": opportunity, "circle": circle}

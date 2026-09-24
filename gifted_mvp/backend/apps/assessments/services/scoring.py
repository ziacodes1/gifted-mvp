"""Deterministic, transparent scoring. No LLM involved anywhere in this module.

For each signal:
- opportunity_count = answered questions that offered at least one option mapped to it
- evidence_count    = selected options that map to it
- score             = weighted picks / opportunities, 0-100 (capped)

Scoring against *opportunities* (not all answers) keeps signal types comparable:
an aptitude signal offered by one puzzle isn't diluted by nine interest questions.
Confidence is deliberately conservative — a ~10-item assessment never yields HIGH.
Interest, aptitude, work style, values and exposure stay separate signals; there is
no combined score.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.evidence.models import EvidenceKind, EvidenceSource
from apps.evidence.services import Contribution, record_evidence
from apps.signals.models import Confidence, LearnerSignal, ResponseSignalMap, SignalCategory

from ..models import AssessmentSession, SessionStatus

# What kind of evidence each signal category represents (never "ability proven").
EVIDENCE_KIND = {
    SignalCategory.INTEREST: EvidenceKind.INTEREST,
    SignalCategory.APTITUDE: EvidenceKind.REASONING,
    SignalCategory.WORK_STYLE: EvidenceKind.ENGAGEMENT,
    SignalCategory.VALUE: EvidenceKind.REFLECTION,
    SignalCategory.EXPOSURE: EvidenceKind.EXPOSURE,
}


@dataclass
class SignalResult:
    key: str
    label: str
    category: str
    score: int
    confidence: str
    evidence_count: int
    opportunity_count: int


def confidence_for(category: str, score: int, evidence_count: int) -> str:
    """LOW or MEDIUM only. Aptitude and exposure stay LOW: one or two puzzles, or a
    self-reported checklist, are early evidence at most."""
    if category in (SignalCategory.APTITUDE, SignalCategory.EXPOSURE):
        return Confidence.LOW
    if category == SignalCategory.INTEREST:
        return Confidence.MEDIUM if evidence_count >= 3 and score >= 50 else Confidence.LOW
    return Confidence.MEDIUM if evidence_count >= 2 else Confidence.LOW


def score_session(session: AssessmentSession) -> list[SignalResult]:
    """Compute deterministic signal scores for a session. Does not persist anything."""
    responses = list(session.responses.prefetch_related("selected_options"))
    if not responses:
        return []

    answered_questions = {r.question_id for r in responses}
    selected = {o.id for r in responses for o in r.selected_options.all()}
    maps = ResponseSignalMap.objects.filter(option__question_id__in=answered_questions).select_related(
        "signal", "option"
    )

    opportunities: dict[int, set[int]] = defaultdict(set)
    raw: dict[int, Decimal] = defaultdict(Decimal)
    evidence: dict[int, int] = defaultdict(int)
    signals = {}
    for m in maps:
        signals[m.signal_id] = m.signal
        opportunities[m.signal_id].add(m.option.question_id)
        if m.option_id in selected:
            raw[m.signal_id] += m.weight
            evidence[m.signal_id] += 1

    results = []
    for signal_id, questions in opportunities.items():
        signal = signals[signal_id]
        score = max(0, min(100, round(float(raw[signal_id]) / len(questions) * 100)))
        results.append(
            SignalResult(
                key=signal.key,
                label=signal.label,
                category=signal.category,
                score=score,
                confidence=confidence_for(signal.category, score, evidence[signal_id]),
                evidence_count=evidence[signal_id],
                opportunity_count=len(questions),
            )
        )
    results.sort(key=lambda r: (-r.score, r.key))
    return results


@transaction.atomic
def complete_session(session: AssessmentSession) -> list[SignalResult]:
    """Score the session, persist LearnerSignal rows (update-in-place, including
    zero-evidence rows so "not tried yet" is known), record ASSESSMENT evidence,
    and mark the session COMPLETED."""
    results = score_session(session)
    signals = {m.signal.key: m.signal for m in ResponseSignalMap.objects.select_related("signal").filter(
        signal__key__in=[r.key for r in results]
    )}

    for r in results:
        LearnerSignal.objects.update_or_create(
            learner_id=session.learner_id,
            signal=signals[r.key],
            defaults={
                "score": r.score,
                "confidence": r.confidence,
                "evidence_count": r.evidence_count,
                "opportunity_count": r.opportunity_count,
                "source_session": session,
            },
        )

    record_evidence(
        learner=session.learner,
        source_type=EvidenceSource.ASSESSMENT,
        source_id=session.id,
        title=session.assessment.title,
        description="Mixed-format discovery assessment.",
        contributions=[
            Contribution(
                r.key,
                EVIDENCE_KIND[r.category],
                Decimal(r.score / 100).quantize(Decimal("0.01")),
                f"{r.evidence_count} of {r.opportunity_count} chances",
            )
            for r in results
            if r.score > 0
        ],
        metadata={"questions_answered": session.responses.count()},
    )

    session.status = SessionStatus.COMPLETED
    session.progress = 100
    session.completed_at = timezone.now()
    session.save(update_fields=["status", "progress", "completed_at"])
    return results

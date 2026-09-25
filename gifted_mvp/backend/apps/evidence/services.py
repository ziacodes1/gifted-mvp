"""The single write path for evidence. Every source (assessment, mission, future
virtual labs...) turns its deterministic observations into `Contribution`s and
calls `record_evidence`. No LLM is involved anywhere here.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.db import IntegrityError, transaction

from apps.signals.models import Signal

from .models import Evidence, SignalEvidence

MAX_WEIGHT_PER_ACTIVITY = Decimal("1.00")  # one activity can never dominate a signal


@dataclass(frozen=True)
class Contribution:
    signal_key: str
    kind: str
    weight: Decimal
    observation: str = ""


def merge_contributions(contributions: list[Contribution]) -> list[Contribution]:
    """Sum per signal, cap at MAX_WEIGHT_PER_ACTIVITY, keep the heaviest kind and
    the first observation. Deterministic and order-stable."""
    merged: dict[str, dict] = {}
    for c in contributions:
        m = merged.setdefault(c.signal_key, {"weight": Decimal("0"), "kinds": {}, "obs": []})
        m["weight"] += Decimal(c.weight)
        m["kinds"][c.kind] = m["kinds"].get(c.kind, Decimal("0")) + Decimal(c.weight)
        if c.observation and c.observation not in m["obs"]:
            m["obs"].append(c.observation)
    out = []
    for key, m in merged.items():
        kind = max(m["kinds"].items(), key=lambda kv: kv[1])[0]
        out.append(
            Contribution(
                signal_key=key,
                kind=kind,
                weight=min(m["weight"], MAX_WEIGHT_PER_ACTIVITY),
                observation="; ".join(m["obs"])[:300],
            )
        )
    return out


def record_evidence(
    *,
    learner,
    source_type: str,
    source_id: int,
    title: str,
    description: str = "",
    contributions: list[Contribution] = (),
    metadata: dict | None = None,
) -> tuple[Evidence, bool]:
    """Idempotent: one Evidence per (source_type, source_id). Returns (evidence, created)."""
    existing = Evidence.objects.filter(source_type=source_type, source_id=source_id).first()
    if existing:
        return existing, False

    merged = merge_contributions(list(contributions))
    signals = {s.key: s for s in Signal.objects.filter(key__in=[c.signal_key for c in merged])}
    unknown = {c.signal_key for c in merged} - set(signals)
    if unknown:
        raise ValueError(f"Unknown signal keys: {sorted(unknown)}")

    try:
        with transaction.atomic():
            evidence = Evidence.objects.create(
                learner=learner,
                source_type=source_type,
                source_id=source_id,
                title=title,
                description=description,
                metadata=metadata or {},
            )
            SignalEvidence.objects.bulk_create(
                SignalEvidence(
                    evidence=evidence,
                    signal=signals[c.signal_key],
                    kind=c.kind,
                    weight=c.weight,
                    observation=c.observation,
                )
                for c in merged
                if c.weight > 0
            )
    except IntegrityError:  # concurrent duplicate — the other writer won
        return Evidence.objects.get(source_type=source_type, source_id=source_id), False
    return evidence, True

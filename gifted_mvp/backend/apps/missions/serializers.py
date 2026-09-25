from rest_framework import serializers

from apps.evidence.models import EvidenceKind

from .models import Mission, MissionAttempt, MissionStep


class MissionStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionStep
        fields = ("id", "key", "type", "title", "prompt", "content", "order")


def mission_summary(mission: Mission) -> dict:
    meta = mission.metadata
    return {
        "id": mission.id,
        "slug": mission.slug,
        "title": mission.title,
        "short_description": mission.short_description,
        "difficulty": mission.difficulty,
        "estimated_minutes": mission.estimated_minutes,
        "time_label": meta.get("time_label", f"{mission.estimated_minutes} min"),
        "activity_label": meta.get("activity_label", "Mission"),
        "focus_areas": meta.get("focus_areas", []),
    }


class MissionDetailSerializer(serializers.ModelSerializer):
    """Server-driven content. Evidence mappings are intentionally NOT exposed."""

    steps = MissionStepSerializer(many=True, read_only=True)

    class Meta:
        model = Mission
        fields = ("id", "slug", "title", "short_description", "context", "difficulty", "estimated_minutes", "steps")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update({k: v for k, v in mission_summary(instance).items() if k not in data})
        data["intro_steps"] = instance.metadata.get("intro_steps", [])
        return data


def evidence_result(evidence) -> dict:
    kinds = dict(EvidenceKind.choices)
    return {
        "id": evidence.id,
        "title": evidence.title,
        "created_at": evidence.created_at,
        "dimensions": [
            {"key": c.signal.key, "label": c.signal.label, "kind": c.kind, "kind_label": kinds[c.kind]}
            for c in evidence.contributions.select_related("signal").order_by("-weight", "signal__label")
        ],
    }


def attempt_payload(attempt: MissionAttempt, evidence=None) -> dict:
    steps = list(attempt.mission.steps.all())
    responses = {r.step_id: r.data for r in attempt.responses.all()}
    next_index = next((i for i, s in enumerate(steps) if s.id not in responses), len(steps))
    return {
        "id": attempt.id,
        "status": attempt.status,
        "started_at": attempt.started_at,
        "completed_at": attempt.completed_at,
        "mission": MissionDetailSerializer(attempt.mission).data,
        "responses": {str(k): v for k, v in responses.items()},
        "next_step_index": next_index,
        "result": evidence_result(evidence) if evidence else None,
    }

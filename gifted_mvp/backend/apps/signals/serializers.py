from rest_framework import serializers

from .models import LearnerSignal


class LearnerSignalSerializer(serializers.ModelSerializer):
    key = serializers.CharField(source="signal.key")
    label = serializers.CharField(source="signal.label")
    category = serializers.CharField(source="signal.category")

    class Meta:
        model = LearnerSignal
        fields = ("key", "label", "category", "score", "confidence", "evidence_count", "opportunity_count", "updated_at")

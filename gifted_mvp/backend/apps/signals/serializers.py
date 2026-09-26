from rest_framework import serializers

from common.i18n import tr

from .models import LearnerSignal


class LearnerSignalSerializer(serializers.ModelSerializer):
    key = serializers.CharField(source="signal.key")
    label = serializers.SerializerMethodField()
    category = serializers.CharField(source="signal.category")

    class Meta:
        model = LearnerSignal
        fields = ("key", "label", "category", "score", "confidence", "evidence_count", "opportunity_count", "updated_at")

    def get_label(self, obj: LearnerSignal) -> str:
        return tr(obj.signal, "label")

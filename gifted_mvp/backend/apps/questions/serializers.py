from rest_framework import serializers

from common.i18n import tr

from .models import Question, QuestionOption


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ("id", "label", "description", "icon", "image", "content", "order")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for f in ("label", "description", "content"):
            data[f] = tr(instance, f)
        return data


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ("id", "type", "prompt", "helper_text", "content", "order", "options")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for f in ("prompt", "helper_text", "content"):
            data[f] = tr(instance, f)
        return data

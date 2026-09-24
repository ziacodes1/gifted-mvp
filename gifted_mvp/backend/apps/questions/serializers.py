from rest_framework import serializers

from .models import Question, QuestionOption


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ("id", "label", "description", "icon", "image", "content", "order")


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ("id", "type", "prompt", "helper_text", "content", "order", "options")

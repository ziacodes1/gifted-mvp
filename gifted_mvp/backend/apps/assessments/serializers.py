from rest_framework import serializers

from apps.questions.serializers import QuestionSerializer
from common.i18n import tr

from .models import Assessment, AssessmentResponse, AssessmentSession


class LatestSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentSession
        fields = ("id", "status", "progress")


class AssessmentListSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    my_latest_session = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = ("id", "title", "slug", "description", "question_count", "my_latest_session")

    def get_question_count(self, obj: Assessment) -> int:
        return sum(section.questions.filter(is_active=True).count() for section in obj.sections.all())

    def get_my_latest_session(self, obj: Assessment):
        user = self.context["request"].user
        session = obj.sessions.filter(learner=user).order_by("-started_at").first()
        return LatestSessionSerializer(session).data if session else None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["title"], data["description"] = tr(instance, "title"), tr(instance, "description")
        return data


class AssessmentDetailSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = ("id", "title", "slug", "description", "question_count")

    def get_question_count(self, obj: Assessment) -> int:
        return sum(section.questions.filter(is_active=True).count() for section in obj.sections.all())

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["title"], data["description"] = tr(instance, "title"), tr(instance, "description")
        return data


class AssessmentSessionSerializer(serializers.ModelSerializer):
    assessment = AssessmentDetailSerializer(read_only=True)
    questions = serializers.SerializerMethodField()
    responses = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    answered_count = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentSession
        fields = (
            "id",
            "status",
            "progress",
            "assessment",
            "questions",
            "responses",
            "total_questions",
            "answered_count",
            "started_at",
            "completed_at",
        )

    def _ordered_questions(self, obj: AssessmentSession):
        return (
            obj.assessment.sections.prefetch_related("questions__options")
            .all()
        )

    def get_questions(self, obj: AssessmentSession):
        questions = []
        for section in self._ordered_questions(obj):
            for q in section.questions.filter(is_active=True):
                questions.append(q)
        return QuestionSerializer(questions, many=True).data

    def get_responses(self, obj: AssessmentSession):
        return {
            str(r.question_id): sorted(o.id for o in r.selected_options.all())
            for r in obj.responses.prefetch_related("selected_options")
        }

    def get_total_questions(self, obj: AssessmentSession) -> int:
        return sum(section.questions.filter(is_active=True).count() for section in obj.assessment.sections.all())

    def get_answered_count(self, obj: AssessmentSession) -> int:
        return obj.responses.count()


class AnswerInputSerializer(serializers.Serializer):
    """`option_id` for single-choice types, `option_ids` for multi-select."""

    question_id = serializers.IntegerField()
    option_id = serializers.IntegerField(required=False)
    option_ids = serializers.ListField(child=serializers.IntegerField(), required=False, max_length=12)

    def validate(self, attrs):
        ids = attrs.get("option_ids") or ([attrs["option_id"]] if "option_id" in attrs else [])
        if not ids:
            raise serializers.ValidationError("Choose an answer.")
        attrs["ids"] = list(dict.fromkeys(ids))
        return attrs

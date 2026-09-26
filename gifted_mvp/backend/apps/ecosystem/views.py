"""Student-only ecosystem API. Parents get 403 (IsStudent); nothing here is parent-visible."""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions.roles import IsStudent

from .models import Category, LearningPath, Mode, OpportunityType, PostType, ReportReason, ResourceType
from .services import catalog, community, for_you


def _error(detail: str, code: int) -> Response:
    return Response({"error": {"detail": detail, "status": code}}, status=code)


def _get(getter, slug):
    try:
        return getter(slug)
    except ObjectDoesNotExist:
        raise NotFound("Not found.")


def _choice(value, choices):
    return value if value in choices else None


def _flag(request, name) -> bool:
    return request.query_params.get(name) in ("1", "true")


class ActionSerializer(serializers.Serializer):
    action = serializers.CharField(max_length=20)


# --- Resources ------------------------------------------------------------------------------


class ResourceListView(APIView):
    """GET ?type=&category=&q=&saved=1&sort=relevant|shortest|newest — personalized list + featured path."""

    permission_classes = [IsStudent]

    def get(self, request):
        p = request.query_params
        return Response(
            catalog.resource_list(
                request.user,
                rtype=_choice(p.get("type"), ResourceType.values),
                category=_choice(p.get("category"), Category.values),
                q=p.get("q", "")[:100],
                saved=_flag(request, "saved"),
                sort=p.get("sort") if p.get("sort") in catalog.SORTS else "relevant",
            )
        )


class ResourceDetailView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, slug):
        return Response(catalog.resource_detail(request.user, _get(catalog.get_resource, slug)))


class ResourceActionView(APIView):
    """POST {action: save|unsave|open|start|complete|reset} → the updated detail."""

    permission_classes = [IsStudent]

    def post(self, request, slug):
        resource = _get(catalog.get_resource, slug)
        data = ActionSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        if data.validated_data["action"] not in catalog.RESOURCE_ACTIONS:
            return _error("Unknown action.", 400)
        try:
            catalog.resource_action(request.user, resource, data.validated_data["action"])
        except catalog.ActionError as exc:
            return _error(str(exc), 400)
        return Response(catalog.resource_detail(request.user, resource))


class LearningPathView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, slug):
        path = _get(lambda s: LearningPath.objects.select_related("organization").get(slug=s, active=True), slug)
        return Response(catalog.path_detail(request.user, path))


# --- Opportunities --------------------------------------------------------------------------


class OpportunityListView(APIView):
    """GET ?category=&mode=ONLINE|IN_PERSON&type=&country=&age=&deadline=closing_soon|all&q=&saved=1"""

    permission_classes = [IsStudent]

    def get(self, request):
        p = request.query_params
        try:
            age = int(p["age"]) if p.get("age") else None
        except ValueError:
            age = None
        return Response(
            catalog.opportunity_list(
                request.user,
                category=_choice(p.get("category"), Category.values),
                mode=_choice(p.get("mode"), Mode.values),
                otype=_choice(p.get("type"), OpportunityType.values),
                country=p.get("country") or None,
                age=age,
                deadline=_choice(p.get("deadline"), ("closing_soon", "all")),
                q=p.get("q", "")[:100],
                saved=_flag(request, "saved"),
            )
        )


class OpportunityDetailView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, slug):
        return Response(catalog.opportunity_detail(request.user, _get(catalog.get_opportunity, slug)))


class OpportunityActionView(APIView):
    """POST {action: save|unsave|view|open_link}. `open_link` records that the learner opened
    the provider's page (APPLICATION_LINK_OPENED) — Gifted never records an application."""

    permission_classes = [IsStudent]

    def post(self, request, slug):
        opportunity = _get(catalog.get_opportunity, slug)
        data = ActionSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            catalog.opportunity_action(request.user, opportunity, data.validated_data["action"])
        except catalog.ActionError as exc:
            return _error(str(exc), 400)
        return Response(catalog.opportunity_detail(request.user, opportunity))


# --- Community ------------------------------------------------------------------------------


class CommunityView(APIView):
    """GET: suggested circles, my circles, all circles, moderated feed, upcoming events."""

    permission_classes = [IsStudent]

    def get(self, request):
        return Response(community.overview(request.user))


class CircleView(APIView):
    """GET circle + its feed · POST join · DELETE leave."""

    permission_classes = [IsStudent]

    def get(self, request, slug):
        return Response(community.circle_detail(request.user, _get(community.get_circle, slug)))

    def post(self, request, slug):
        community.join(request.user, _get(community.get_circle, slug))
        return Response(community.overview(request.user))

    def delete(self, request, slug):
        community.leave(request.user, _get(community.get_circle, slug))
        return Response(community.overview(request.user))


class PostSerializer(serializers.Serializer):
    circle = serializers.SlugField()
    body = serializers.CharField(max_length=community.POST_MAX, trim_whitespace=True)
    post_type = serializers.ChoiceField(choices=PostType.values, default=PostType.SHARE)


class PostCreateView(APIView):
    """POST {circle, body, post_type} → 201; the post waits for moderation (PENDING)."""

    permission_classes = [IsStudent]
    throttle_scope = "community_post"

    def post(self, request):
        data = PostSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        circle = _get(community.get_circle, data.validated_data["circle"])
        try:
            community.create_post(request.user, circle, data.validated_data["body"], data.validated_data["post_type"])
        except community.CommunityError as exc:
            return _error(str(exc), exc.status)
        return Response(community.overview(request.user), status=status.HTTP_201_CREATED)


class ReportSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=ReportReason.values, default=ReportReason.OTHER)


class PostReportView(APIView):
    """POST {reason} → 204. Idempotent per learner; enough reports send the post back to review."""

    permission_classes = [IsStudent]
    throttle_scope = "community_report"

    def post(self, request, post_id):
        data = ReportSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            community.report_post(request.user, post_id, data.validated_data["reason"])
        except community.CommunityError as exc:
            return _error(str(exc), exc.status)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ForYouView(APIView):
    """GET: one resource, one opportunity and one circle for Home / Passport (deterministic)."""

    permission_classes = [IsStudent]

    def get(self, request):
        return Response(for_you(request.user))

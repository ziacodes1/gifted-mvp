from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions.roles import IsParent

from .services import (
    build_parent_overview,
    connect_with_code,
    connected_learners,
    ensure_parent_insight,
    get_connected_learner,
)


class ParentChildrenView(APIView):
    permission_classes = [IsParent]

    def get(self, request):
        return Response(
            [
                {"id": c.id, "display_name": c.full_name.strip() or c.email.split("@")[0]}
                for c in connected_learners(request.user)
            ]
        )


class ConnectInput(serializers.Serializer):
    code = serializers.CharField(max_length=12)


class ParentConnectView(APIView):
    """POST {code}: connect to a learner via their GFT-xxxxx code."""

    permission_classes = [IsParent]

    def post(self, request):
        payload = ConnectInput(data=request.data)
        payload.is_valid(raise_exception=True)
        learner = connect_with_code(request.user, payload.validated_data["code"])
        return Response({"id": learner.id, "display_name": learner.full_name or learner.email.split("@")[0]})


class ParentChildOverviewView(APIView):
    """GET: one aggregate for the parent dashboard + insights page. No model calls."""

    permission_classes = [IsParent]

    def get(self, request, learner_id):
        return Response(build_parent_overview(get_connected_learner(request.user, learner_id)))


class ParentChildInsightView(APIView):
    """POST: get-or-generate the Parent Insight for the current evidence version (idempotent)."""

    permission_classes = [IsParent]

    def post(self, request, learner_id):
        learner = get_connected_learner(request.user, learner_id)
        return Response({"parent_insight": ensure_parent_insight(learner)})

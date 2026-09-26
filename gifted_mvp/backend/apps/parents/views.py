from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from django.http import Http404
from rest_framework import status

from common.permissions.roles import IsParent, IsStudent

from .services import (
    build_parent_overview,
    connect_with_code,
    disconnect_parent,
    issue_code,
    parent_access,
    revoke_code,
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
    code = serializers.CharField(max_length=20)


class ParentConnectView(APIView):
    """POST {code}: connect to a learner with the single-use code the learner generated
    (GFT-XXXX-XXXX). Invalid/expired/revoked/used codes → 404. Throttled."""

    permission_classes = [IsParent]
    throttle_scope = "parent_connect"

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
    throttle_scope = "ai_generation"

    def post(self, request, learner_id):
        learner = get_connected_learner(request.user, learner_id)
        return Response({"parent_insight": ensure_parent_insight(learner)})


class StudentParentAccessView(APIView):
    """Learner side. GET: current valid code (if any) + connected parents."""

    permission_classes = [IsStudent]

    def get(self, request):
        return Response(parent_access(request.user))


class StudentParentCodeView(APIView):
    """POST: generate a new single-use, expiring code (replaces the old one). DELETE: revoke it."""

    permission_classes = [IsStudent]

    def post(self, request):
        entry = issue_code(request.user)
        return Response({"code": entry.code, "expires_at": entry.expires_at}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        revoke_code(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class StudentParentLinkView(APIView):
    """DELETE: the learner removes a connected parent."""

    permission_classes = [IsStudent]

    def delete(self, request, parent_id):
        if not disconnect_parent(request.user, parent_id):
            raise Http404
        return Response(status=status.HTTP_204_NO_CONTENT)

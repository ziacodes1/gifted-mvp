from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions.roles import IsStudent

from .services import build_passport


class MyPassportView(APIView):
    """GET: the authenticated student's Passport in one payload. Never calls an LLM."""

    permission_classes = [IsStudent]

    def get(self, request):
        return Response(build_passport(request.user))

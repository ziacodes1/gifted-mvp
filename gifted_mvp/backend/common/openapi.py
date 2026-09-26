"""OpenAPI generation (drf-spectacular) tuned for this codebase.

Most endpoints are plain APIViews returning read models, so there is no serializer to infer.
Instead of documenting them wrongly, the schema lists every endpoint with its domain tag, the
role that may call it, and the view's docstring; request bodies are documented where a
serializer exists.
"""
from drf_spectacular.openapi import AutoSchema
from rest_framework.permissions import AllowAny, IsAuthenticated

from common.permissions.roles import IsAdmin, IsParent, IsStudent

ROLE_TEXT = {
    IsStudent: "Access: STUDENT only — the caller's own data (other learners → 404).",
    IsParent: "Access: PARENT only — connected learners' parent-safe read model (never diary, Companion chats, mood or private reflections).",
    IsAdmin: "Access: ADMIN only.",
    AllowAny: "Access: public.",
    IsAuthenticated: "Access: any signed-in user.",
}


class GiftedAutoSchema(AutoSchema):
    def get_tags(self):
        parts = [p for p in self.path.split("/") if p and not p.startswith("{")]
        # /api/v1/<domain>/...
        domain = parts[2] if len(parts) > 2 else "api"
        return [{"parent": "parent-mode", "parent-access": "parent-access (student)"}.get(domain, domain)]

    def get_description(self):
        base = super().get_description() or ""
        perms = getattr(self.view, "permission_classes", []) or []
        roles = [ROLE_TEXT[p] for p in perms if p in ROLE_TEXT]
        scope = getattr(self.view, "throttle_scope", None)
        extra = [*roles] + ([f"Rate limited (scope `{scope}`)."] if scope else [])
        return "\n\n".join(x for x in [base.strip(), *extra] if x)

    def _get_serializer(self):
        # Read-model APIViews have no serializer: document the endpoint without guessing a body.
        serializer_class = getattr(self.view, "serializer_class", None)
        if serializer_class:
            return serializer_class()
        if hasattr(self.view, "get_serializer_class"):
            try:
                return self.view.get_serializer()
            except Exception:  # noqa: BLE001 — generic view without a serializer
                return None
        return None

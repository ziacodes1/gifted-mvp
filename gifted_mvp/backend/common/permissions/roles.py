"""Role-based permissions. Extensible: add new roles/classes without touching views."""
from rest_framework.permissions import BasePermission

from apps.accounts.models import Role


class HasRole(BasePermission):
    """Base class; subclass and set `required_role`."""

    required_role: str | None = None

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and user.role == self.required_role
        )


class IsStudent(HasRole):
    required_role = Role.STUDENT


class IsParent(HasRole):
    required_role = Role.PARENT


class IsAdmin(HasRole):
    required_role = Role.ADMIN

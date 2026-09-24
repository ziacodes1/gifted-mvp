"""Custom User with email login + extensible role system.

Kept from the start (never postponed) so the whole schema hangs off a stable
AUTH_USER_MODEL. Learner/parent profile detail lives in their own domains later.
"""
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from .managers import UserManager


class Role(models.TextChoices):
    STUDENT = "STUDENT", "Student"
    PARENT = "PARENT", "Parent"
    ADMIN = "ADMIN", "Admin"


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(
        max_length=16, choices=Role.choices, default=Role.STUDENT, db_index=True
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Django admin access
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email + password prompted by createsuperuser

    class Meta:
        db_table = "accounts_user"

    def __str__(self) -> str:
        return f"{self.email} ({self.role})"

    @property
    def is_student(self) -> bool:
        return self.role == Role.STUDENT

    @property
    def is_parent(self) -> bool:
        return self.role == Role.PARENT

    @property
    def is_admin_role(self) -> bool:
        return self.role == Role.ADMIN

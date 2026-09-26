from common.admin.locking import ReadOnlyAdmin
from django.contrib import admin

from .models import Passport


@admin.register(Passport)
class PassportAdmin(ReadOnlyAdmin):
    list_display = ("id", "learner", "status", "version", "source_session", "updated_at")
    list_filter = ("status",)

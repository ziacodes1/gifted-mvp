from django.apps import AppConfig


class DiaryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.diary"
    label = "diary"

    def ready(self):
        from . import signals  # noqa: F401  (removes photo files with their rows)

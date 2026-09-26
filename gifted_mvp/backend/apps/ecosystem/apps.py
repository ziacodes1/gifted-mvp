from django.apps import AppConfig


class EcosystemConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ecosystem"
    label = "ecosystem"
    verbose_name = "Ecosystem (organizations, resources, opportunities, community)"

"""Root URL config. All API lives under /api/v1/."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from common.observability import health_live, health_ready

api_v1 = [
    path("health/", health_live, name="health"),  # kept for existing probes/clients
    path("health/live/", health_live, name="health-live"),
    path("health/ready/", health_ready, name="health-ready"),
    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.assessments.urls")),
    path("", include("apps.signals.urls")),
    path("", include("apps.ai.urls")),
    path("", include("apps.passports.urls")),
    path("", include("apps.missions.urls")),
    path("", include("apps.parents.urls")),
    path("", include("apps.companion.urls")),
    path("", include("apps.diary.urls")),
    path("", include("apps.engagement.urls")),
    path("", include("apps.today.urls")),
]

if settings.API_DOCS_ENABLED:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    api_v1 += [
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path("docs/", SpectacularSwaggerView.as_view(url_name="v1:schema"), name="docs"),
    ]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1, "v1"))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

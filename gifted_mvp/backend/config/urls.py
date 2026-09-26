"""Root URL config. All API lives under /api/v1/."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.accounts.views import health

api_v1 = [
    path("health/", health, name="health"),
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

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1, "v1"))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

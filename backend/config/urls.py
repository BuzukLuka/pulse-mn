from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from apps.common import ops


def health(_request):
    return JsonResponse({"status": "ok", "service": "pulse-mn-backend"})


urlpatterns = [
    path("", health),
    path("health/", health),
    path("ops/run/", ops.run),
    path("django-admin/", admin.site.urls),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.catalog.urls")),
    path("api/v1/", include("apps.content.urls")),
    path("api/v1/", include("apps.review.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/", include("apps.audit.urls")),
    path("api/v1/", include("apps.pledges.urls")),
    path("api/v1/", include("apps.statistics.urls")),
    path("api/v1/", include("apps.complaints.urls")),
    path("api/v1/", include("apps.newsroom.urls")),
    path("api/v1/", include("apps.worldnews.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

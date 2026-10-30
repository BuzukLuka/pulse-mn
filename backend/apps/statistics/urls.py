from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (IndicatorViewSet, PublicCompare, PublicIndicators, PublicSeries, SourceViewSet,
                    backup, restore_value)

router = DefaultRouter()
router.register("admin/stats/sources", SourceViewSet, basename="stat-sources")
router.register("admin/stats/indicators", IndicatorViewSet, basename="stat-indicators")
urlpatterns = [
    path("stats/indicators/", PublicIndicators.as_view()),
    path("stats/indicators/<int:pk>/series/", PublicSeries.as_view()),
    path("stats/compare/", PublicCompare.as_view()),
    path("admin/stats/history/<int:history_id>/restore/", restore_value),
    path("admin/backup/", backup),
] + router.urls

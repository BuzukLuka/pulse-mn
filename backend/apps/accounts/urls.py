from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (AdminStatsView, AdminUserViewSet, AdminVerifyView, ExperienceView, JournalistListView,
                    JournalistPublicView, LoginView, MeView, PortfolioView, RegisterView)

router = DefaultRouter()
router.register("admin/users", AdminUserViewSet, basename="admin-users")

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("profile/experiences/", ExperienceView.as_view()),
    path("profile/portfolio/", PortfolioView.as_view()),
    path("journalists/", JournalistListView.as_view()),
    path("journalists/<int:pk>/", JournalistPublicView.as_view()),
    path("admin/users/<int:pk>/verify/", AdminVerifyView.as_view()),
    path("admin/stats/", AdminStatsView.as_view()),
    path("", include(router.urls)),
]

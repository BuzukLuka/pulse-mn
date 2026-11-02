from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (MembershipEndView, MyMembershipsView, NewsroomDashboardViewSet, NewsroomListView,
                    NewsroomPublicView, PurchaseViewSet, RatingSuggestView, RatingView, RequestVerificationView)

router = DefaultRouter()
router.register("newsroom", NewsroomDashboardViewSet, basename="newsroom")
router.register("purchases", PurchaseViewSet, basename="purchases")

urlpatterns = [
    path("newsrooms/", NewsroomListView.as_view()),
    path("newsrooms/<int:pk>/", NewsroomPublicView.as_view()),
    path("memberships/", MyMembershipsView.as_view()),
    path("memberships/<int:pk>/end/", MembershipEndView.as_view()),
    path("auth/request-verification/", RequestVerificationView.as_view()),
    path("ratings/", RatingView.as_view()),
    path("ratings/suggest/", RatingSuggestView.as_view()),
] + router.urls

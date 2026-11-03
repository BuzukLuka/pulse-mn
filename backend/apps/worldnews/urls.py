from django.urls import path

from .views import WorldNewsRefreshView, WorldNewsSourcesView, WorldNewsView

urlpatterns = [
    path("world-news/", WorldNewsView.as_view()),
    path("world-news/sources/", WorldNewsSourcesView.as_view()),
    path("world-news/refresh/", WorldNewsRefreshView.as_view()),
]

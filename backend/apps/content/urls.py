from rest_framework.routers import DefaultRouter
from .views import AdminContentViewSet, MyContentViewSet, PublicNewsViewSet

router = DefaultRouter()
router.register("content", MyContentViewSet, basename="my-content")
router.register("news", PublicNewsViewSet, basename="news")
router.register("admin/content", AdminContentViewSet, basename="admin-content")
urlpatterns = router.urls

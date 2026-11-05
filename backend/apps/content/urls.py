from rest_framework.routers import DefaultRouter
from .comments import CommentViewSet
from .views import AdminContentViewSet, MyContentViewSet, PublicNewsViewSet

router = DefaultRouter()
router.register("content", MyContentViewSet, basename="my-content")
router.register("news", PublicNewsViewSet, basename="news")
router.register("admin/content", AdminContentViewSet, basename="admin-content")
router.register("comments", CommentViewSet, basename="comments")
urlpatterns = router.urls

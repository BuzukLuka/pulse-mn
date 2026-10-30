from rest_framework.routers import DefaultRouter
from .views import AdminComplaintViewSet, MyComplaintViewSet

router = DefaultRouter()
router.register("complaints", MyComplaintViewSet, basename="complaints")
router.register("admin/complaints", AdminComplaintViewSet, basename="admin-complaints")
urlpatterns = router.urls

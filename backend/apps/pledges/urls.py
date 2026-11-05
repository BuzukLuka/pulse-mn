from rest_framework.routers import DefaultRouter
from .views import AdminPledgeUpdateViewSet, PledgeViewSet, PoliticianViewSet

router = DefaultRouter()
router.register("pledges/politicians", PoliticianViewSet, basename="politicians")
router.register("pledges", PledgeViewSet, basename="pledges")
router.register("admin/pledge-updates", AdminPledgeUpdateViewSet, basename="admin-pledge-updates")
urlpatterns = router.urls

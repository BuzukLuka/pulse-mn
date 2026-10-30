from rest_framework.routers import DefaultRouter
from .views import PledgeViewSet, PoliticianViewSet

router = DefaultRouter()
router.register("pledges/politicians", PoliticianViewSet, basename="politicians")
router.register("pledges", PledgeViewSet, basename="pledges")
urlpatterns = router.urls

from rest_framework.routers import DefaultRouter

from buyers.views import BuyerCarPreferenceViewSet, BuyerViewSet

router = DefaultRouter()
router.register(r"buyers", BuyerViewSet, basename="buyer")
router.register(r"buyer-preferences", BuyerCarPreferenceViewSet, basename="buyer-preference")

urlpatterns = router.urls

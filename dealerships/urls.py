from rest_framework.routers import DefaultRouter

from dealerships.views import DealershipInventoryViewSet, DealershipViewSet

router = DefaultRouter()
router.register(r'dealerships', DealershipViewSet, basename='dealership')
router.register(r'dealership-inventory', DealershipInventoryViewSet, basename='dealership-inventory')

urlpatterns = router.urls

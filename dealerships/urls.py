from rest_framework.routers import DefaultRouter

from dealerships.views import (
    DealershipCarPreferenceViewSet,
    DealershipInventoryViewSet,
    DealershipViewSet,
    PurchaseLogViewSet,
    SaleRecordViewSet,
)

router = DefaultRouter()
router.register(r'dealerships', DealershipViewSet, basename='dealership')
router.register(r'dealership-inventory', DealershipInventoryViewSet, basename='dealership-inventory')
router.register(r'dealership-preferences', DealershipCarPreferenceViewSet, basename='dealership-preference')
router.register(r'sale-records', SaleRecordViewSet, basename='sale-record')
router.register(r'purchase-logs', PurchaseLogViewSet, basename='purchase-log')

urlpatterns = router.urls

from rest_framework.routers import DefaultRouter
from suppliers.views import SupplierInventoryViewSet, SupplierViewSet

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'supplier-inventory', SupplierInventoryViewSet, basename='supplier-inventory')

urlpatterns = router.urls

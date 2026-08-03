from rest_framework.routers import DefaultRouter

from suppliers.views import SupplierInventoryViewSet, SupplierPromotionViewSet, SupplierViewSet

router = DefaultRouter()
router.register(r"suppliers", SupplierViewSet, basename="supplier")
router.register(r"supplier-inventory", SupplierInventoryViewSet, basename="supplier-inventory")
router.register(r"supplier-promotions", SupplierPromotionViewSet, basename="supplier-promotion")

urlpatterns = router.urls

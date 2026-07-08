from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from suppliers.filters import SupplierFilter, SupplierInventoryFilter, SupplierPromotionFilter
from suppliers.models import Supplier, SupplierInventory, SupplierPromotion
from suppliers.serializers import (
    SupplierInventorySerializer,
    SupplierPromotionSerializer,
    SupplierSerializer,
)


@extend_schema_view(
    list=extend_schema(summary='Список поставщиков', tags=['Suppliers']),
    create=extend_schema(summary='Создать поставщика', tags=['Suppliers']),
    retrieve=extend_schema(summary='Получить поставщика', tags=['Suppliers']),
    update=extend_schema(summary='Обновить поставщика', tags=['Suppliers']),
    partial_update=extend_schema(summary='Частично обновить поставщика', tags=['Suppliers']),
    destroy=extend_schema(summary='Удалить поставщика', tags=['Suppliers']),
)
class SupplierViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet для управления поставщиками.
    - Просмотр - auth
    - Запись - admin.
    """

    queryset = Supplier.objects.filter(is_deleted=False)
    serializer_class = SupplierSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SupplierFilter
    search_fields = ['name', 'country']
    ordering_fields = ['name', 'balance', 'country', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        """Мягкое удаление."""
        instance.is_deleted = True
        instance.save()


@extend_schema_view(
    list=extend_schema(summary='Список позиций склада поставщика', tags=['Supplier Inventory']),
    create=extend_schema(summary='Добавить позицию на склад поставщика', tags=['Supplier Inventory']),
    retrieve=extend_schema(summary='Получить позицию склада поставщика', tags=['Supplier Inventory']),
    update=extend_schema(summary='Обновить позицию склада поставщика', tags=['Supplier Inventory']),
    partial_update=extend_schema(summary='Частично обновить позицию склада поставщика', tags=['Supplier Inventory']),
    destroy=extend_schema(summary='Удалить позицию склада поставщика', tags=['Supplier Inventory']),
)
class SupplierInventoryViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet для управления складом поставщика.
    - Просмотр доступен аутентифицированным пользователям.
    - Запись — только администраторам.
    """

    queryset = SupplierInventory.objects.select_related('supplier', 'car').all()
    serializer_class = SupplierInventorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SupplierInventoryFilter
    search_fields = ['supplier__name', 'car__brand', 'car__model_name']
    ordering_fields = ['quantity', 'price_per_unit', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminUser()]
        return [IsAuthenticated()]


@extend_schema_view(
    list=extend_schema(summary='Список акций поставщиков', tags=['Supplier Promotions']),
    create=extend_schema(summary='Создать акцию поставщика', tags=['Supplier Promotions']),
    retrieve=extend_schema(summary='Получить акцию поставщика', tags=['Supplier Promotions']),
    update=extend_schema(summary='Обновить акцию поставщика', tags=['Supplier Promotions']),
    partial_update=extend_schema(summary='Частично обновить акцию поставщика', tags=['Supplier Promotions']),
    destroy=extend_schema(summary='Удалить акцию поставщика', tags=['Supplier Promotions']),
)
class SupplierPromotionViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Акции поставщиков со скидками на машины.
    Используются SupplierPriceEngine при расчёте effective_price в Celery-задаче.
    - Просмотр - auth.
    - Запись - admin.
    """

    queryset = SupplierPromotion.objects.select_related('supplier', 'car').all()
    serializer_class = SupplierPromotionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SupplierPromotionFilter
    search_fields = ['supplier__name', 'car__brand', 'car__model_name', 'title']
    ordering_fields = ['discount_percent', 'start_date', 'end_date', 'created_at']
    ordering = ['-start_date']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from dealerships.filters import (
    DealershipBestSupplierFilter,
    DealershipCarPreferenceFilter,
    DealershipFilter,
    DealershipInventoryFilter,
    PurchaseLogFilter,
    SaleRecordFilter,
)
from dealerships.models import (
    Dealership,
    DealershipBestSupplier,
    DealershipCarPreference,
    DealershipInventory,
    PurchaseLog,
    SaleRecord,
)
from dealerships.serializers import (
    DealershipBestSupplierSerializer,
    DealershipCarPreferenceSerializer,
    DealershipInventorySerializer,
    DealershipSerializer,
    PurchaseLogSerializer,
    SaleRecordSerializer,
)


@extend_schema_view(
    list=extend_schema(summary='Список автосалонов', tags=['Dealerships']),
    create=extend_schema(summary='Создать автосалон', tags=['Dealerships']),
    retrieve=extend_schema(summary='Получить автосалон', tags=['Dealerships']),
    update=extend_schema(summary='Обновить автосалон', tags=['Dealerships']),
    partial_update=extend_schema(summary='Частично обновить автосалон', tags=['Dealerships']),
    destroy=extend_schema(summary='Удалить автосалон', tags=['Dealerships']),
)
class DealershipViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet для управления автосалонами.
    - Просмотр - auth.
    - Запись - admin.
    """

    queryset = Dealership.objects.filter(is_deleted=False)
    serializer_class = DealershipSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DealershipFilter
    search_fields = ['name', 'location']
    ordering_fields = ['name', 'balance', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()


@extend_schema_view(
    list=extend_schema(summary='Список позиций склада автосалона', tags=['Dealership Inventory']),
    create=extend_schema(summary='Добавить позицию на склад', tags=['Dealership Inventory']),
    retrieve=extend_schema(summary='Получить позицию склада', tags=['Dealership Inventory']),
    update=extend_schema(summary='Обновить позицию склада', tags=['Dealership Inventory']),
    partial_update=extend_schema(summary='Частично обновить позицию склада', tags=['Dealership Inventory']),
    destroy=extend_schema(summary='Удалить позицию склада', tags=['Dealership Inventory']),
)
class DealershipInventoryViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet для управления складом автосалона.
    - Просмотр - auth.
    - Запись - admin.
    """

    queryset = DealershipInventory.objects.select_related('dealership', 'car').all()
    serializer_class = DealershipInventorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DealershipInventoryFilter
    search_fields = ['dealership__name', 'car__brand', 'car__model_name']
    ordering_fields = ['quantity', 'price_per_unit', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminUser()]
        return [IsAuthenticated()]


@extend_schema_view(
    list=extend_schema(summary='Список предпочтений автосалона по машинам', tags=['Dealership Preferences']),
    create=extend_schema(summary='Добавить предпочтение', tags=['Dealership Preferences']),
    retrieve=extend_schema(summary='Получить предпочтение', tags=['Dealership Preferences']),
    update=extend_schema(summary='Обновить предпочтение', tags=['Dealership Preferences']),
    partial_update=extend_schema(summary='Частично обновить предпочтение', tags=['Dealership Preferences']),
    destroy=extend_schema(summary='Удалить предпочтение', tags=['Dealership Preferences']),
)
class DealershipCarPreferenceViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Предпочтительные машины dealership'а.
    - Просмотр - auth.
    - Запись - admin.
    """

    queryset = DealershipCarPreference.objects.select_related('dealership', 'car').all()
    serializer_class = DealershipCarPreferenceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DealershipCarPreferenceFilter
    search_fields = ['dealership__name', 'car__brand', 'car__model_name']
    ordering_fields = ['min_stock', 'target_stock', 'created_at']
    ordering = ['dealership__name', 'car__brand']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminUser()]
        return [IsAuthenticated()]


@extend_schema_view(
    list=extend_schema(summary='История продаж автосалонов', tags=['Sale Records']),
    retrieve=extend_schema(summary='Запись о продаже', tags=['Sale Records']),
)
class SaleRecordViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Read-only. История продаж - создаётся автоматически при принятии Offer.
    - Только auth пользователи.
    """

    queryset = SaleRecord.objects.select_related('dealership', 'car').all()
    serializer_class = SaleRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SaleRecordFilter
    search_fields = ['dealership__name', 'car__brand', 'car__model_name']
    ordering_fields = ['quantity_sold', 'sold_at', 'created_at']
    ordering = ['-sold_at']


@extend_schema_view(
    list=extend_schema(summary='Лог закупок автосалонов', tags=['Purchase Logs']),
    retrieve=extend_schema(summary='Запись лога закупки', tags=['Purchase Logs']),
)
class PurchaseLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Аудит-лог каждой попытки закупки из Celery-задачи.
    purchased=True  - покупка совершена.
    purchased=False - пропущено, причина в поле reason.
    - Только admin.
    """

    queryset = PurchaseLog.objects.select_related('dealership', 'supplier', 'car').all()
    serializer_class = PurchaseLogSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PurchaseLogFilter
    search_fields = ['dealership__name', 'supplier__name', 'car__brand', 'car__model_name', 'reason']
    ordering_fields = ['quantity', 'total_cost', 'purchased', 'created_at']
    ordering = ['-created_at']

@extend_schema_view(
    list=extend_schema(summary='Лучшие поставщики по моделям', tags=['Best Suppliers']),
    retrieve=extend_schema(summary='Лучший поставщик для пары автосалон × модель', tags=['Best Suppliers']),
)
class DealershipBestSupplierViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Актуальный список лучших поставщиков по каждой модели для каждого автосалона.
    Обновляется задачей run_supplier_ranking (04:00 UTC).
    supplier=null = на данный момент ни один поставщик не имеет этой машины в наличии.
    - Только auth.
    """

    queryset = (
        DealershipBestSupplier.objects
        .select_related('dealership', 'car', 'supplier')
        .all()
    )
    serializer_class = DealershipBestSupplierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DealershipBestSupplierFilter
    search_fields = ['dealership__name', 'car__brand', 'car__model_name', 'supplier__name', 'reason']
    ordering_fields = ['effective_price', 'updated_at']
    ordering = ['-updated_at']

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from dealerships.filters import DealershipFilter, DealershipInventoryFilter
from dealerships.models import Dealership, DealershipInventory
from dealerships.serializers import DealershipInventorySerializer, DealershipSerializer


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

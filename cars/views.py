from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from cars.filters import CarFilter
from cars.models import Car
from cars.serializers import CarSerializer


@extend_schema_view(
    list=extend_schema(summary="Список автомобилей", tags=["Cars"]),
    create=extend_schema(summary="Создать автомобиль", tags=["Cars"]),
    retrieve=extend_schema(summary="Получить автомобиль", tags=["Cars"]),
    update=extend_schema(summary="Обновить автомобиль", tags=["Cars"]),
    partial_update=extend_schema(summary="Частично обновить автомобиль", tags=["Cars"]),
    destroy=extend_schema(summary="Удалить автомобиль", tags=["Cars"]),
)
class CarViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet для управления автомобилями.
    - Просмотр - auth
    - Создание, изменение и удаление - admin
    """

    queryset = Car.objects.filter(is_deleted=False)
    serializer_class = CarSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CarFilter
    search_fields = ["brand", "model_name"]
    ordering_fields = ["year", "brand", "model_name", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

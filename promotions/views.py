from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from promotions.filters import PromotionFilter
from promotions.models import Promotion
from promotions.serializers import PromotionSerializer


@extend_schema_view(
    list=extend_schema(summary="Список акций", tags=["Promotions"]),
    create=extend_schema(summary="Создать акцию", tags=["Promotions"]),
    retrieve=extend_schema(summary="Получить акцию", tags=["Promotions"]),
    update=extend_schema(summary="Обновить акцию", tags=["Promotions"]),
    partial_update=extend_schema(summary="Частично обновить акцию", tags=["Promotions"]),
    destroy=extend_schema(summary="Удалить акцию", tags=["Promotions"]),
)
class PromotionViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet для управления промоушенами.
    - Просмотр - auth
    - Создание, изменение и удаление - admin.
    """

    queryset = Promotion.objects.select_related("dealership").all()
    serializer_class = PromotionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PromotionFilter
    search_fields = ["title", "description", "dealership__name"]
    ordering_fields = ["title", "discount_percent", "start_date", "end_date", "created_at"]
    ordering = ["-start_date"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return [IsAuthenticated()]

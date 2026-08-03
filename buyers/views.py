from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from buyers.filters import BuyerCarPreferenceFilter, BuyerFilter
from buyers.models import Buyer, BuyerCarPreference
from buyers.serializers import (
    BuyerCarPreferenceSerializer,
    BuyerSerializer,
    BuyerStatisticsSerializer,
)
from buyers.statistics import BuyerStatisticsService


@extend_schema_view(
    list=extend_schema(summary="Список покупателей", tags=["Buyers"]),
    retrieve=extend_schema(summary="Профиль покупателя", tags=["Buyers"]),
    create=extend_schema(summary="Создать покупателя", tags=["Buyers"]),
    update=extend_schema(summary="Обновить покупателя", tags=["Buyers"]),
    partial_update=extend_schema(summary="Частично обновить покупателя", tags=["Buyers"]),
    destroy=extend_schema(summary="Удалить покупателя", tags=["Buyers"]),
)
class BuyerViewSet(viewsets.ModelViewSet):
    queryset = Buyer.objects.select_related("user").filter(is_deleted=False)
    serializer_class = BuyerSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BuyerFilter
    search_fields = ["user__username", "user__email"]
    ordering_fields = ["balance", "created_at"]
    ordering = ["-created_at"]

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

    def get_permissions(self):
        if self.action == "statistics":
            return [IsAuthenticated()]
        return [IsAdminUser()]

    @extend_schema(
        summary="Статистика покупателя",
        tags=["Buyers"],
        responses={200: BuyerStatisticsSerializer},
    )
    @action(detail=True, methods=["get"], url_path="statistics")
    def statistics(self, request, pk=None):
        data = BuyerStatisticsService().get_statistics(int(pk), request.user)
        return Response(BuyerStatisticsSerializer(data).data)


@extend_schema_view(
    list=extend_schema(summary="Предпочтения покупателей", tags=["Buyer Preferences"]),
    retrieve=extend_schema(summary="Предпочтение покупателя", tags=["Buyer Preferences"]),
    create=extend_schema(summary="Добавить предпочтение", tags=["Buyer Preferences"]),
    update=extend_schema(summary="Обновить предпочтение", tags=["Buyer Preferences"]),
    partial_update=extend_schema(
        summary="Частично обновить предпочтение", tags=["Buyer Preferences"]
    ),
    destroy=extend_schema(summary="Удалить предпочтение", tags=["Buyer Preferences"]),
)
class BuyerCarPreferenceViewSet(viewsets.ModelViewSet):
    """
    Управление предпочтениями покупателя.
    - Просмотр, управление своими предпочтениями - auth.
    - Просмотр чужих - admin.
    """

    serializer_class = BuyerCarPreferenceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BuyerCarPreferenceFilter
    search_fields = ["car__brand", "car__model_name", "buyer__user__username"]
    ordering_fields = ["max_price", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return BuyerCarPreference.objects.select_related("buyer__user", "car").all()
        return BuyerCarPreference.objects.select_related("buyer__user", "car").filter(
            buyer__user=self.request.user
        )

    def get_permissions(self):
        return [IsAuthenticated()]

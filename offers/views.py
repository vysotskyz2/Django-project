from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from accounts.permissions import IsEmailVerified
from offers.filters import OfferFilter
from offers.models import Offer, OfferStatus
from offers.serializers import OfferSerializer, OfferStatusUpdateSerializer
from dealerships.models import SaleRecord

@extend_schema_view(
    list=extend_schema(summary='Список офферов', tags=['Offers']),
    create=extend_schema(summary='Создать оффер', tags=['Offers']),
    retrieve=extend_schema(summary='Получить оффер', tags=['Offers']),
    update=extend_schema(summary='Обновить оффер', tags=['Offers']),
    partial_update=extend_schema(summary='Частично обновить оффер', tags=['Offers']),
    destroy=extend_schema(summary='Удалить оффер', tags=['Offers']),
)
class OfferViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet для управления офферами.
    - Просмотр, создание -auth
    - Изменение статуса и удаление - admin.
    """

    queryset = Offer.objects.select_related('dealership', 'supplier', 'car').filter(is_deleted=False)
    serializer_class = OfferSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OfferFilter
    search_fields = ['dealership__name', 'supplier__name', 'car__brand', 'car__model_name']
    ordering_fields = ['created_at', 'quantity', 'offered_price', 'status']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy', 'set_status'):
            return [IsAdminUser()]
        if self.action == 'create':
            return [IsAuthenticated(), IsEmailVerified()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'set_status':
            return OfferStatusUpdateSerializer
        return OfferSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

    @extend_schema(
        summary='Изменить статус оффера',
        tags=['Offers'],
        request=OfferStatusUpdateSerializer,
        responses={200: OfferSerializer},
    )
    @action(detail=True, methods=['patch'], url_path='set-status')
    def set_status(self, request, pk=None):
        offer = self.get_object()
        serializer = OfferStatusUpdateSerializer(offer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        serializer.save()

        if new_status == OfferStatus.ACCEPTED:
            SaleRecord.objects.create(
                dealership=offer.dealership,
                car=offer.car,
                quantity_sold=offer.quantity,
            )

        return Response(OfferSerializer(offer).data, status=status.HTTP_200_OK)


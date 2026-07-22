from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound, PermissionDenied
from buyers.repositories import BuyerRepository
from offers.repositories import OfferRepository


class BuyerStatisticsService:
    def __init__(self) -> None:
        self._buyer_repo = BuyerRepository()
        self._offer_repo = OfferRepository()

    def get_statistics(self, buyer_id: int, requesting_user: User) -> dict:
        try:
            buyer = self._buyer_repo.get_active_or_404(buyer_id)
        except ObjectDoesNotExist:
            raise NotFound(detail='Buyer not found.')

        if not requesting_user.is_staff and buyer.user_id != requesting_user.pk:
            raise PermissionDenied('Вы можете просматривать только свою статистику.')

        purchases_qs = self._offer_repo.get_accepted_for_buyer(buyer_id)

        total_spent = Decimal('0.00')
        purchases = []
        for offer in purchases_qs:
            unit_price = (
                offer.offered_price.amount
                if offer.offered_price is not None
                else Decimal('0.00')
            )
            line_total = unit_price * offer.quantity
            total_spent += line_total
            purchases.append({
                'offer_id': offer.pk,
                'car_id': offer.car_id,
                'car': str(offer.car),
                'dealership_id': offer.dealership_id,
                'dealership_name': (
                    offer.dealership.name if offer.dealership_id else None
                ),
                'quantity': offer.quantity,
                'price_per_unit': unit_price,
                'price_per_unit_currency': 'USD',
                'total': line_total,
                'total_currency': 'USD',
                'purchased_at': offer.updated_at,
            })

        return {
            'buyer_id': buyer.pk,
            'username': buyer.user.username,
            'total_spent': total_spent,
            'total_spent_currency': 'USD',
            'purchases_count': len(purchases),
            'balance': buyer.balance.amount,
            'balance_currency': str(buyer.balance.currency),
            'purchases': purchases,
        }

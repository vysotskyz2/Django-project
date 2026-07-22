from typing import Any
from django.db.models import QuerySet
from moneyed import Money
from buyers.models import Buyer, BuyerCarPreference
from cars.models import Car


class BuyerRepository:
    def get_active_ids(self) -> list[int]:
        return list(Buyer.objects.filter(is_deleted=False).values_list('id', flat=True))

    def get_active_by_id(self, buyer_id: int) -> Buyer | None:
        try:
            return Buyer.objects.select_related('user').get(pk=buyer_id, is_deleted=False)
        except Buyer.DoesNotExist:
            return None

    def get_active_or_404(self, buyer_id: int) -> Buyer:
        return Buyer.objects.select_related('user').get(pk=buyer_id, is_deleted=False)

    def lock_for_update(self, buyer_id: int) -> Buyer:
        return Buyer.objects.select_related('user').select_for_update().get(pk=buyer_id)

    def deduct_balance(self, buyer: Buyer, amount: Money) -> None:
        buyer.balance -= amount
        buyer.save(update_fields=['balance', 'balance_currency'])

    def add_balance(self, buyer: Buyer, amount: Money) -> None:
        buyer.balance += amount
        buyer.save(update_fields=['balance', 'balance_currency'])


class BuyerCarPreferenceRepository:
    def get_preferred_for_buyer(self, buyer: Buyer) -> QuerySet[BuyerCarPreference]:
        return (
            BuyerCarPreference.objects
            .filter(buyer=buyer)
            .select_related('car')
        )

    def get_by_buyer_and_car(self, buyer: Buyer, car: Car) -> BuyerCarPreference | None:
        return BuyerCarPreference.objects.filter(buyer=buyer, car=car).first()

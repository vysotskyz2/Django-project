from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound

from dealerships.repositories import (
    DealershipInventoryRepository,
    DealershipRepository,
    PurchaseLogRepository,
    SaleRecordRepository,
)
from offers.repositories import OfferRepository


class DealershipStatisticsService:
    def __init__(self) -> None:
        self._dealer_repo = DealershipRepository()
        self._sale_repo = SaleRecordRepository()
        self._offer_repo = OfferRepository()
        self._purchase_repo = PurchaseLogRepository()
        self._inv_repo = DealershipInventoryRepository()

    def get_statistics(self, dealership_id: int) -> dict:
        try:
            dealership = self._dealer_repo.get_active_or_404(dealership_id)
        except ObjectDoesNotExist:
            raise NotFound(detail="Dealership not found.") from None

        cars_sold = self._sale_repo.get_total_sold_all_cars(dealership)

        accepted_offers = self._offer_repo.get_accepted_for_dealership(dealership_id)
        unique_buyers = (
            accepted_offers.exclude(buyer__isnull=True).values("buyer_id").distinct().count()
        )
        accepted_offers_count = accepted_offers.count()

        revenue = Decimal("0.00")
        for offer in accepted_offers:
            if offer.offered_price is not None:
                revenue += offer.offered_price.amount * offer.quantity

        purchase_spend = self._purchase_repo.get_total_spend(dealership)
        inventory_units = self._inv_repo.get_total_units(dealership)
        profit = revenue - purchase_spend

        return {
            "dealership_id": dealership.pk,
            "dealership_name": dealership.name,
            "cars_sold": cars_sold,
            "unique_buyers": unique_buyers,
            "accepted_offers": accepted_offers_count,
            "revenue": revenue,
            "revenue_currency": "USD",
            "purchase_spend": purchase_spend,
            "purchase_spend_currency": "USD",
            "profit": profit,
            "profit_currency": "USD",
            "balance": dealership.balance.amount,
            "balance_currency": str(dealership.balance.currency),
            "inventory_units": inventory_units,
        }

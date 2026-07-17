from django.db.models import QuerySet
from offers.models import Offer, OfferStatus
from moneyed import Money

class OfferRepository:
    def get_pending_buyer_offers(self, buyer) -> QuerySet[Offer]:
        return (
            Offer.objects
            .filter(buyer=buyer, status=OfferStatus.PENDING, is_deleted=False)
            .select_related('car', 'dealership', 'buyer__user')
        )

    def get_buyer_ids_with_pending_offers(self) -> list[int]:
        return list(
            Offer.objects
            .filter(status=OfferStatus.PENDING, is_deleted=False, buyer__isnull=False)
            .values_list('buyer_id', flat=True)
            .distinct()
        )

    def accept(self, offer: Offer, dealership, price_per_unit, reason: str) -> Offer:
        offer.status = OfferStatus.ACCEPTED
        offer.dealership = dealership
        offer.offered_price = Money(price_per_unit, 'USD')
        offer.reason = reason
        offer.save(update_fields=['status', 'dealership', 'offered_price', 'offered_price_currency', 'reason', 'updated_at'])
        return offer

    def reject(self, offer: Offer, reason: str) -> Offer:
        offer.status = OfferStatus.REJECTED
        offer.reason = reason
        offer.save(update_fields=['status', 'reason', 'updated_at'])
        return offer

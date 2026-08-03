from django.db.models import Count, QuerySet
from moneyed import Money

from offers.models import Offer, OfferStatus


class OfferRepository:
    def get_pending_buyer_offers(self, buyer) -> QuerySet[Offer]:
        return Offer.objects.filter(
            buyer=buyer, status=OfferStatus.PENDING, is_deleted=False
        ).select_related("car", "dealership", "buyer__user")

    def get_accepted_counts_by_dealership(
        self,
        buyer,
        dealership_ids: list[int],
    ) -> dict[int, int]:
        qs = (
            Offer.objects.filter(
                buyer=buyer,
                dealership_id__in=dealership_ids,
                status=OfferStatus.ACCEPTED,
            )
            .values("dealership_id")
            .annotate(count=Count("id"))
        )
        return {item["dealership_id"]: item["count"] for item in qs}

    def get_buyer_ids_with_pending_offers(self) -> list[int]:
        return list(
            Offer.objects.filter(status=OfferStatus.PENDING, is_deleted=False, buyer__isnull=False)
            .values_list("buyer_id", flat=True)
            .distinct()
        )

    def get_accepted_for_dealership(self, dealership_id: int) -> QuerySet[Offer]:
        return Offer.objects.filter(
            dealership_id=dealership_id, status=OfferStatus.ACCEPTED, is_deleted=False
        ).select_related("car", "buyer__user")

    def get_accepted_for_buyer(self, buyer_id: int) -> QuerySet[Offer]:
        return (
            Offer.objects.filter(buyer_id=buyer_id, status=OfferStatus.ACCEPTED, is_deleted=False)
            .select_related("car", "dealership")
            .order_by("-updated_at")
        )

    def accept(self, offer: Offer, dealership, price_per_unit, reason: str) -> Offer:
        offer.status = OfferStatus.ACCEPTED
        offer.dealership = dealership
        offer.offered_price = Money(price_per_unit, "USD")
        offer.reason = reason
        offer.save(
            update_fields=[
                "status",
                "dealership",
                "offered_price",
                "offered_price_currency",
                "reason",
                "updated_at",
            ]
        )
        return offer

    def reject(self, offer: Offer, reason: str) -> Offer:
        offer.status = OfferStatus.REJECTED
        offer.reason = reason
        offer.save(update_fields=["status", "reason", "updated_at"])
        return offer

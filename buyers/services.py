from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from loguru import logger
from moneyed import Money
from buyers.repositories import BuyerCarPreferenceRepository, BuyerRepository
from dealerships.models import DealershipInventory
from dealerships.repositories import (
    DealershipInventoryRepository,
    DealershipRepository,
    SaleRecordRepository,
)
from offers.repositories import OfferRepository
from promotions.repositories import PromotionRepository

class BuyerOfferService:
    def __init__(self) -> None:
        self._buyer_repo = BuyerRepository()
        self._pref_repo = BuyerCarPreferenceRepository()
        self._offer_repo = OfferRepository()
        self._dealer_repo = DealershipRepository()
        self._inv_repo = DealershipInventoryRepository()
        self._sale_repo = SaleRecordRepository()
        self._promo_repo = PromotionRepository()

    def get_buyer_ids_with_pending_offers(self) -> list[int]:
        return self._offer_repo.get_buyer_ids_with_pending_offers()

    def run_for_buyer(self, buyer_id: int) -> None:
        buyer = self._buyer_repo.get_active_by_id(buyer_id)
        if buyer is None:
            logger.warning(
                'BuyerOfferService: buyer id={} not found or deleted',
                buyer_id,
            )
            return

        logger.info(
            'BuyerOfferService: START buyer="{}" (id={})',
            buyer.user.username, buyer_id,
        )

        if not buyer.is_email_verified:
            logger.warning(
                'BuyerOfferService: buyer="{}" email not verified - skipping all offers',
                buyer.user.username,
            )
            return

        if buyer.balance.amount <= 0:
            logger.warning(
                'BuyerOfferService: buyer="{}" balance={} - skipping all offers',
                buyer.user.username, buyer.balance,
            )
            return

        prefs = {p.car_id: p for p in self._pref_repo.get_preferred_for_buyer(buyer)}

        pending_offers = list(self._offer_repo.get_pending_buyer_offers(buyer))

        if not pending_offers:
            logger.info(
                'BuyerOfferService: buyer="{}" has no pending offers',
                buyer.user.username,
            )
            return

        accepted = rejected = 0
        for offer in pending_offers:
            pref = prefs.get(offer.car_id)
            result = self._process_offer(buyer, offer, pref)
            if result:
                accepted += 1
            else:
                rejected += 1

        logger.info(
            'BuyerOfferService: DONE buyer="{}" accepted={} rejected={}',
            buyer.user.username, accepted, rejected,
        )

    def _process_offer(self, buyer, offer, pref) -> bool:
        max_price: Decimal = offer.max_budget.amount
        if pref is not None and pref.max_price.amount < max_price:
            max_price = pref.max_price.amount

        effective_limit = min(max_price, buyer.balance.amount)

        candidates = self._find_matching_inventories(offer.car, effective_limit)

        if not candidates:
            reason = (
                f'no dealership found for {offer.car} '
                f'within budget {effective_limit} USD '
                f'(buyer balance={buyer.balance.amount} USD)'
            )
            self._offer_repo.reject(offer, reason)
            logger.info(
                'BuyerOfferService: REJECTED buyer="{}" car="{}" - {}',
                buyer.user.username, offer.car, reason,
            )
            return False

        best_inv = self._rank_and_pick(buyer, candidates)
        deal_price: Decimal = best_inv.price_per_unit.amount

        try:
            self._execute_deal(buyer=buyer, offer=offer, inventory=best_inv, price=deal_price)
            return True
        except Exception as exc:
            reason = f'deal execution failed: {exc}'
            self._offer_repo.reject(offer, reason)
            logger.error(
                'BuyerOfferService: FAILED buyer="{}" car="{}" dealership="{}" - {}',
                buyer.user.username, offer.car, best_inv.dealership.name, exc,
            )
            return False

    def _find_matching_inventories(self, car, price_limit: Decimal) -> list:
        return self._inv_repo.find_matching_for_car(car, price_limit)

    def _rank_and_pick(self, buyer, candidates: list):
        today = timezone.now().date()

        dealership_ids = [inv.dealership_id for inv in candidates]

        active_promo_dealership_ids = self._promo_repo.get_active_dealership_ids(
            dealership_ids, today,
        )
        accepted_counts = self._offer_repo.get_accepted_counts_by_dealership(
            buyer, dealership_ids,
        )

        def score(inv):
            dealership_id = inv.dealership_id
            price = inv.price_per_unit.amount
            has_promo = dealership_id in active_promo_dealership_ids
            sale_history = accepted_counts.get(dealership_id, 0)
            return (price, 0 if has_promo else 1, -sale_history)

        return min(candidates, key=score)

    @transaction.atomic
    def _execute_deal(self, *, buyer, offer, inventory, price: Decimal) -> None:
        total_cost = Money(price * offer.quantity, 'USD')
        price_money = Money(price, 'USD')
        dealership = inventory.dealership

        buyer_locked = self._buyer_repo.lock_for_update(buyer.pk)
        dealership_locked = self._dealer_repo.lock_for_update(dealership.pk)

        if buyer_locked.balance.amount < total_cost.amount:
            raise ValueError(
                f'Insufficient buyer balance: need {total_cost.amount} USD, '
                f'have {buyer_locked.balance.amount} USD'
            )

        try:
            inv_locked = self._inv_repo.lock_for_dealership_and_car(dealership, offer.car)
        except DealershipInventory.DoesNotExist:
            raise ValueError(
                f'Dealership "{dealership.name}" has no inventory record for {offer.car}'
            )

        if inv_locked.quantity < offer.quantity:
            raise ValueError(
                f'Insufficient stock at "{dealership.name}": '
                f'need {offer.quantity}, have {inv_locked.quantity}'
            )

        self._buyer_repo.deduct_balance(buyer_locked, total_cost)
        self._dealer_repo.add_balance(dealership_locked, total_cost)

        self._inv_repo.deduct_stock(inv_locked, offer.quantity)

        reason = (
            f'purchased from "{dealership.name}" for {price} USD per unit, '
            f'total {total_cost.amount} USD'
        )
        self._offer_repo.accept(offer, dealership_locked, price, reason)

        self._sale_repo.create(
            dealership=dealership,
            car=offer.car,
            quantity_sold=offer.quantity,
        )

        logger.info(
            'BuyerOfferService: ACCEPTED buyer="{}" car="{}" dealership="{}" '
            'qty={} price={} USD total={} USD',
            buyer.user.username, offer.car, dealership.name,
            offer.quantity, price, total_cost.amount,
        )

from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import timedelta
from loguru import logger
from moneyed import Money
from dealerships.models import SaleRecord, DealershipInventory, PurchaseLog
from suppliers.models import SupplierPromotion, SupplierInventory

RESTOCK_THRESHOLD = 2
SKIP_THRESHOLD = 14

class DemandCalculator:
    @staticmethod
    def calculate_daily_demand(dealership, car, n_days: int = 30) -> float:
        since = timezone.now() - timedelta(days=n_days)
        result = SaleRecord.objects.filter(
            dealership=dealership,
            car=car,
            sold_at__gte=since,
        ).aggregate(total=Sum('quantity_sold'))
        total = result['total'] or 0
        return total / n_days

    @staticmethod
    def days_of_stock(dealership, car, n_days: int = 30) -> float:
        try:
            inv = DealershipInventory.objects.get(dealership=dealership, car=car)
            current_stock = inv.quantity
        except DealershipInventory.DoesNotExist:
            return 0.0

        daily_demand = DemandCalculator.calculate_daily_demand(dealership, car, n_days)
        if daily_demand == 0:
            return float('inf')
        return current_stock / daily_demand

    @staticmethod
    def needs_restock(dealership, car, n_days: int = 30) -> bool:
        days = DemandCalculator.days_of_stock(dealership, car, n_days)
        return days < SKIP_THRESHOLD

    @staticmethod
    def get_current_stock(dealership, car) -> int:
        try:
            inv = DealershipInventory.objects.get(dealership=dealership, car=car)
            return inv.quantity
        except DealershipInventory.DoesNotExist:
            return 0

class SupplierPriceEngine:
    @staticmethod
    def get_effective_price(supplier_inventory) -> Decimal:

        today = timezone.now().date()
        base_price: Decimal = supplier_inventory.price_per_unit.amount

        best_discount = Decimal('0')
        promotions = SupplierPromotion.objects.filter(
            supplier=supplier_inventory.supplier,
            start_date__lte=today,
            end_date__gte=today,
        ).filter(
            Q(car=supplier_inventory.car) | Q(car__isnull=True)
        )

        for promo in promotions:
            if promo.discount_percent > best_discount:
                best_discount = promo.discount_percent

        effective_price = base_price * (1 - best_discount / Decimal('100'))
        return effective_price

    @staticmethod
    def get_best_offer(car, quantity: int, budget_amount: Decimal):

        candidates = SupplierInventory.objects.select_related(
            'supplier', 'car'
        ).filter(
            car=car,
            quantity__gte=quantity,
            supplier__is_deleted=False,
        )

        best_inv = None
        best_price: Decimal | None = None

        for inv in candidates:
            effective_price = SupplierPriceEngine.get_effective_price(inv)
            total_cost = effective_price * quantity

            if total_cost > budget_amount:
                logger.debug(
                    'SupplierPriceEngine: supplier=%s car=%s price=%s total=%s '
                    'exceeds budget=%s — skipping',
                    inv.supplier.name, car, effective_price, total_cost, budget_amount,
                )
                continue

            if best_price is None or effective_price < best_price:
                best_inv = inv
                best_price = effective_price

        if best_inv is None:
            return None
        return best_inv, best_price

class PurchaseService:
    @staticmethod
    @transaction.atomic
    def execute_purchase(
        dealership,
        supplier,
        car,
        quantity: int,
        price_per_unit: Decimal,
        reason: str,
    ):
        total_cost: Decimal = price_per_unit * quantity
        total_money = Money(total_cost, 'USD')
        price_money = Money(price_per_unit, 'USD')

        dealership_locked = dealership.__class__.objects.select_for_update().get(pk=dealership.pk)
        supplier_locked = supplier.__class__.objects.select_for_update().get(pk=supplier.pk)

        if dealership_locked.balance.amount < total_cost:
            raise ValueError(
                f'Insufficient balance for dealership "{dealership.name}": '
                f'need {total_cost} USD, have {dealership_locked.balance.amount} USD'
            )

        try:
            sup_inv = SupplierInventory.objects.select_for_update().get(
                supplier=supplier_locked, car=car
            )
        except SupplierInventory.DoesNotExist:
            raise ValueError(
                f'Supplier "{supplier.name}" has no inventory record for {car}'
            )

        if sup_inv.quantity < quantity:
            raise ValueError(
                f'Insufficient stock at supplier "{supplier.name}" for {car}: '
                f'need {quantity}, have {sup_inv.quantity}'
            )

        dealership_locked.balance -= total_money
        dealership_locked.save(update_fields=['balance', 'balance_currency'])

        supplier_locked.balance += total_money
        supplier_locked.save(update_fields=['balance', 'balance_currency'])

        sup_inv.quantity -= quantity
        sup_inv.save(update_fields=['quantity'])

        deal_inv, created = DealershipInventory.objects.get_or_create(
            dealership=dealership,
            car=car,
            defaults={'quantity': 0, 'price_per_unit': price_money},
        )
        deal_inv.quantity += quantity
        deal_inv.save(update_fields=['quantity'])

        log = PurchaseLog.objects.create(
            dealership=dealership,
            supplier=supplier,
            car=car,
            quantity=quantity,
            price_per_unit=price_money,
            total_cost=total_money,
            purchased=True,
            reason=reason,
        )

        logger.info(
            'PurchaseService: BOUGHT dealership="%s" supplier="%s" car="%s" '
            'qty=%d price_per_unit=%s USD total=%s USD | %s',
            dealership.name, supplier.name, car,
            quantity, price_per_unit, total_cost, reason,
        )

        return log

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from loguru import logger
from moneyed import Money
from dealerships.repositories import (
    DealershipRepository,
    DealershipInventoryRepository,
    DealershipCarPreferenceRepository,
    PurchaseLogRepository,
    SaleRecordRepository,
)
from suppliers.repositories import (
    SupplierRepository,
    SupplierInventoryRepository,
    SupplierPromotionRepository,
)


RESTOCK_THRESHOLD = 2
SKIP_THRESHOLD = 14

class DemandService:
    def __init__(self) -> None:
        self._sale_repo = SaleRecordRepository()
        self._inv_repo = DealershipInventoryRepository()

    def calculate_daily_demand(self, dealership, car, n_days: int = 30) -> float:
        total = self._sale_repo.get_total_sold(dealership, car, n_days)
        return total / n_days

    def days_of_stock(self, dealership, car, n_days: int = 30) -> float:
        current_stock = self._inv_repo.get_current_stock(dealership, car)
        if current_stock == 0:
            return 0.0
        daily_demand = self.calculate_daily_demand(dealership, car, n_days)
        if daily_demand == 0:
            return float('inf')
        return current_stock / daily_demand

    def get_current_stock(self, dealership, car) -> int:
        return self._inv_repo.get_current_stock(dealership, car)


class SupplierPriceService:
    def __init__(self) -> None:
        self._promo_repo = SupplierPromotionRepository()
        self._sup_inv_repo = SupplierInventoryRepository()

    def get_effective_price(self, supplier_inventory) -> Decimal:
        today = timezone.now().date()
        base_price: Decimal = supplier_inventory.price_per_unit.amount

        best_discount = Decimal('0')
        promotions = self._promo_repo.get_active_for(
            supplier=supplier_inventory.supplier,
            car=supplier_inventory.car,
            today=today,
        )
        for promo in promotions:
            if promo.discount_percent > best_discount:
                best_discount = promo.discount_percent

        return base_price * (1 - best_discount / Decimal('100'))

    def get_best_offer(self, car, quantity: int, budget_amount: Decimal):
        candidates = self._sup_inv_repo.get_available_for_car(car, quantity)

        best_inv = None
        best_price: Decimal | None = None

        for inv in candidates:
            effective_price = self.get_effective_price(inv)
            total_cost = effective_price * quantity

            if total_cost > budget_amount:
                logger.debug(
                    'SupplierPriceService: supplier={} car={} price={} total={} '
                    'exceeds budget={} - skipping',
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
    def __init__(self) -> None:
        self._dealer_repo = DealershipRepository()
        self._deal_inv_repo = DealershipInventoryRepository()
        self._supplier_repo = SupplierRepository()
        self._sup_inv_repo = SupplierInventoryRepository()
        self._log_repo = PurchaseLogRepository()

    @transaction.atomic
    def execute_purchase(
        self,
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

        dealership_locked = self._dealer_repo.lock_for_update(dealership.pk)
        supplier_locked = self._supplier_repo.lock_for_update(supplier.pk)

        if dealership_locked.balance.amount < total_cost:
            raise ValueError(
                f'Insufficient balance for dealership "{dealership.name}": '
                f'need {total_cost} USD, have {dealership_locked.balance.amount} USD'
            )

        try:
            sup_inv = self._sup_inv_repo.lock_for_update(supplier_locked, car)
        except Exception:
            raise ValueError(
                f'Supplier "{supplier.name}" has no inventory record for {car}'
            )

        if sup_inv.quantity < quantity:
            raise ValueError(
                f'Insufficient stock at supplier "{supplier.name}" for {car}: '
                f'need {quantity}, have {sup_inv.quantity}'
            )

        self._dealer_repo.deduct_balance(dealership_locked, total_money)
        self._supplier_repo.add_balance(supplier_locked, total_money)
        self._sup_inv_repo.deduct_stock(sup_inv, quantity)

        deal_inv = self._deal_inv_repo.get_or_create(
            dealership=dealership,
            car=car,
            default_price=price_money,
        )
        self._deal_inv_repo.add_stock(deal_inv, quantity)

        log = self._log_repo.log_purchase(
            dealership=dealership,
            supplier=supplier,
            car=car,
            quantity=quantity,
            price_per_unit=price_money,
            total_cost=total_money,
            reason=reason,
        )

        logger.info(
            'PurchaseService: BOUGHT dealership="{}" supplier="{}" car="{}" '
            'qty={} price_per_unit={} USD total={} USD | {}',
            dealership.name, supplier.name, car,
            quantity, price_per_unit, total_cost, reason,
        )
        return log


class ProcurementService:
    def __init__(self) -> None:
        self._dealer_repo = DealershipRepository()
        self._inv_repo = DealershipInventoryRepository()
        self._pref_repo = DealershipCarPreferenceRepository()
        self._log_repo = PurchaseLogRepository()
        self._demand_svc = DemandService()
        self._price_svc = SupplierPriceService()
        self._purchase_svc = PurchaseService()

    def run_for_dealership(self, dealership_id: int, n_days: int = 30) -> None:
        dealership = self._dealer_repo.get_active_by_id(dealership_id)
        if dealership is None:
            logger.warning(
                'ProcurementService: dealership id={} not found or deleted - skipping',
                dealership_id,
            )
            return

        logger.info(
            'ProcurementService: START dealership="{}" (id={})',
            dealership.name, dealership_id,
        )

        processed_car_ids: set[int] = set()

        preferences = self._pref_repo.get_preferred_for_dealership(dealership)
        for pref in preferences:
            self._try_purchase(
                dealership=dealership,
                car=pref.car,
                min_stock=pref.min_stock,
                target_stock=pref.target_stock,
                n_days=n_days,
                reason_prefix='preferred_car',
            )
            processed_car_ids.add(pref.car_id)

        logger.info(
            'ProcurementService: Pass 1 done - {} preferred cars checked',
            len(processed_car_ids),
        )

        inventory_items = (
            self._inv_repo.get_all_for_dealership(dealership)
            .exclude(car_id__in=processed_car_ids)
        )

        pass2_count = 0
        for inv in inventory_items:
            car = inv.car
            days = self._demand_svc.days_of_stock(dealership, car, n_days)

            if days >= SKIP_THRESHOLD:
                logger.debug(
                    'ProcurementService: SKIP (demand ok) dealership="{}" car="{}" days_of_stock={:.1f}',
                    dealership.name, car, days,
                )
                continue

            pref = self._pref_repo.get_by_dealership_and_car(dealership, car)
            min_stock = pref.min_stock if pref else 5
            target_stock = pref.target_stock if pref else 10

            self._try_purchase(
                dealership=dealership,
                car=car,
                min_stock=min_stock,
                target_stock=target_stock,
                n_days=n_days,
                reason_prefix='demand_restock',
            )
            pass2_count += 1

        logger.info(
            'ProcurementService: DONE dealership="{}" pass1={} pass2={}',
            dealership.name, len(processed_car_ids), pass2_count,
        )

    def get_active_dealership_ids(self) -> list[int]:
        return self._dealer_repo.get_active_ids()

    def _try_purchase(
        self,
        *,
        dealership,
        car,
        min_stock: int,
        target_stock: int,
        n_days: int,
        reason_prefix: str,
    ) -> None:
        current_stock = self._demand_svc.get_current_stock(dealership, car)
        quantity_to_buy = target_stock - current_stock
        days = self._demand_svc.days_of_stock(dealership, car, n_days)

        if current_stock >= min_stock:
            reason = (
                f'{reason_prefix}: sufficient stock '
                f'(current={current_stock} >= min={min_stock}, days_of_stock={days:.1f})'
            )
            logger.info('ProcurementService SKIP: dealership="{}" car="{}" - {}', dealership.name, car, reason)
            self._log_repo.log_skip(dealership=dealership, car=car, reason=reason)
            return

        budget_amount: Decimal = dealership.balance.amount
        result = self._price_svc.get_best_offer(car, quantity_to_buy, budget_amount)

        if result is None:
            reason = (
                f'{reason_prefix}: no supplier available '
                f'(car={car}, qty={quantity_to_buy}, budget={budget_amount} USD, days_of_stock={days:.1f})'
            )
            logger.warning('ProcurementService SKIP: dealership="{}" car="{}" - {}', dealership.name, car, reason)
            self._log_repo.log_skip(dealership=dealership, car=car, reason=reason)
            return

        supplier_inv, effective_price = result
        supplier = supplier_inv.supplier
        total_cost: Decimal = effective_price * quantity_to_buy

        if budget_amount < total_cost:
            reason = (
                f'{reason_prefix}: insufficient balance '
                f'(need={total_cost} USD, have={budget_amount} USD, '
                f'car={car}, qty={quantity_to_buy})'
            )
            logger.warning('ProcurementService SKIP: dealership="{}" car="{}" - {}', dealership.name, car, reason)
            self._log_repo.log_skip(dealership=dealership, car=car, reason=reason)
            return

        purchase_reason = (
            f'{reason_prefix}: stock={current_stock} min={min_stock} '
            f'buying={quantity_to_buy} supplier="{supplier.name}" '
            f'price={effective_price} USD/unit total={total_cost} USD days_of_stock={days:.1f}'
        )
        try:
            self._purchase_svc.execute_purchase(
                dealership=dealership,
                supplier=supplier,
                car=car,
                quantity=quantity_to_buy,
                price_per_unit=effective_price,
                reason=purchase_reason,
            )
        except Exception as exc:
            reason = f'{reason_prefix}: purchase failed — {exc}'
            logger.error(
                'ProcurementService FAILED: dealership="{}" car="{}" supplier="{}" - {}',
                dealership.name, car, supplier.name, exc,
            )
            self._log_repo.log_skip(
                dealership=dealership, car=car, reason=reason, supplier=supplier
            )

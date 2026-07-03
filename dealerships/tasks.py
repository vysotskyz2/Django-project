from decimal import Decimal

from celery import shared_task
from loguru import logger
from dealerships.models import Dealership, DealershipCarPreference, DealershipInventory, PurchaseLog
from dealerships.services import (
    RESTOCK_THRESHOLD,
    SKIP_THRESHOLD,
    DemandCalculator,
    PurchaseService,
    SupplierPriceEngine,
)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_dealership_procurement(self, n_days: int = 30):
    try:
        dealership_ids = list(
            Dealership.objects.filter(is_deleted=False).values_list('id', flat=True)
        )
        logger.info(
            'run_dealership_procurement: dispatching %d subtasks (n_days=%d)',
            len(dealership_ids), n_days,
        )
        for dealership_id in dealership_ids:
            process_dealership_procurement.delay(dealership_id, n_days)

        return {'dispatched': len(dealership_ids)}

    except Exception as exc:
        logger.exception('run_dealership_procurement: unexpected error — %s', exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_dealership_procurement(self, dealership_id: int, n_days: int = 30):
    try:
        dealership = Dealership.objects.get(pk=dealership_id, is_deleted=False)
    except Dealership.DoesNotExist:
        logger.warning(
            'process_dealership_procurement: dealership id=%d not found or deleted — skipping',
            dealership_id,
        )
        return

    logger.info(
        'process_dealership_procurement: START dealership="%s" (id=%d)',
        dealership.name, dealership_id,
    )

    processed_car_ids: set[int] = set()

    preferences = (
        DealershipCarPreference.objects
        .filter(dealership=dealership, is_preferred=True)
        .select_related('car')
    )

    for pref in preferences:
        _try_purchase(
            dealership=dealership,
            car=pref.car,
            min_stock=pref.min_stock,
            target_stock=pref.target_stock,
            n_days=n_days,
            reason_prefix='preferred_car',
        )
        processed_car_ids.add(pref.car_id)

    logger.info(
        'process_dealership_procurement: Pass 1 done — %d preferred cars checked',
        len(processed_car_ids),
    )

    inventory_items = (
        DealershipInventory.objects
        .filter(dealership=dealership)
        .exclude(car_id__in=processed_car_ids)
        .select_related('car')
    )

    pass2_count = 0
    for inv in inventory_items:
        car = inv.car
        days = DemandCalculator.days_of_stock(dealership, car, n_days)

        if days >= SKIP_THRESHOLD:
            logger.debug(
                'process_dealership_procurement: SKIP (demand ok) '
                'dealership="%s" car="%s" days_of_stock=%.1f',
                dealership.name, car, days,
            )
            continue

        pref = DealershipCarPreference.objects.filter(
            dealership=dealership, car=car
        ).first()
        min_stock = pref.min_stock if pref else 5
        target_stock = pref.target_stock if pref else 10

        _try_purchase(
            dealership=dealership,
            car=car,
            min_stock=min_stock,
            target_stock=target_stock,
            n_days=n_days,
            reason_prefix='demand_restock',
        )
        pass2_count += 1

    logger.info(
        'process_dealership_procurement: DONE dealership="%s" '
        'pass1=%d pass2=%d',
        dealership.name, len(processed_car_ids), pass2_count,
    )


def _try_purchase(
    dealership,
    car,
    min_stock: int,
    target_stock: int,
    n_days: int,
    reason_prefix: str,
) -> None:
    current_stock = DemandCalculator.get_current_stock(dealership, car)
    quantity_to_buy = target_stock - current_stock
    days = DemandCalculator.days_of_stock(dealership, car, n_days)

    if current_stock >= min_stock:
        reason = (
            f'{reason_prefix}: sufficient stock '
            f'(current={current_stock} >= min={min_stock}, '
            f'days_of_stock={days:.1f})'
        )
        logger.info('_try_purchase SKIP: dealership="%s" car="%s" — %s',
                    dealership.name, car, reason)
        PurchaseLog.objects.create(
            dealership=dealership,
            car=car,
            quantity=0,
            purchased=False,
            reason=reason,
        )
        return

    budget_amount: Decimal = dealership.balance.amount
    result = SupplierPriceEngine.get_best_offer(car, quantity_to_buy, budget_amount)

    if result is None:
        reason = (
            f'{reason_prefix}: no supplier available '
            f'(car={car}, qty={quantity_to_buy}, budget={budget_amount} USD, '
            f'days_of_stock={days:.1f})'
        )
        logger.warning('_try_purchase SKIP: dealership="%s" car="%s" — %s',
                       dealership.name, car, reason)
        PurchaseLog.objects.create(
            dealership=dealership,
            car=car,
            quantity=0,
            purchased=False,
            reason=reason,
        )
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
        logger.warning('_try_purchase SKIP: dealership="%s" car="%s" — %s',
                       dealership.name, car, reason)
        PurchaseLog.objects.create(
            dealership=dealership,
            car=car,
            quantity=0,
            purchased=False,
            reason=reason,
        )
        return

    purchase_reason = (
        f'{reason_prefix}: stock={current_stock} min={min_stock} '
        f'buying={quantity_to_buy} supplier="{supplier.name}" '
        f'price={effective_price} USD/unit total={total_cost} USD '
        f'days_of_stock={days:.1f}'
    )
    try:
        PurchaseService.execute_purchase(
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
            '_try_purchase FAILED: dealership="%s" car="%s" supplier="%s" — %s',
            dealership.name, car, supplier.name, exc,
        )
        PurchaseLog.objects.create(
            dealership=dealership,
            car=car,
            quantity=0,
            purchased=False,
            reason=reason,
        )

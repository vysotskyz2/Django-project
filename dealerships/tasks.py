from celery import shared_task
from loguru import logger
from dealerships.services import ProcurementService, SupplierRankingService

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_dealership_procurement(self, n_days: int = 30):
    try:
        svc = ProcurementService()
        dealership_ids = svc.get_active_dealership_ids()
        logger.info(
            'run_dealership_procurement: dispatching {} subtasks (n_days={})',
            len(dealership_ids), n_days,
        )
        for dealership_id in dealership_ids:
            process_dealership_procurement.delay(dealership_id, n_days)
        return {'dispatched': len(dealership_ids)}
    except Exception as exc:
        logger.exception('run_dealership_procurement: unexpected error - {}', exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_dealership_procurement(self, dealership_id: int, n_days: int = 30):
    ProcurementService().run_for_dealership(dealership_id, n_days)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_supplier_ranking(self):
    try:
        svc = SupplierRankingService()
        dealership_ids = svc.get_active_dealership_ids()
        logger.info(
            'run_supplier_ranking: dispatching {} subtasks',
            len(dealership_ids),
        )
        for dealership_id in dealership_ids:
            process_dealership_supplier_ranking.delay(dealership_id)
        return {'dispatched': len(dealership_ids)}
    except Exception as exc:
        logger.exception('run_supplier_ranking: unexpected error - {}', exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_dealership_supplier_ranking(self, dealership_id: int):
    SupplierRankingService().run_for_dealership(dealership_id)

from celery import shared_task
from loguru import logger

from buyers.services import BuyerOfferService


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_buyer_offer_processing(self):
    try:
        svc = BuyerOfferService()
        buyer_ids = svc.get_buyer_ids_with_pending_offers()
        logger.info(
            "run_buyer_offer_processing: dispatching {} subtasks",
            len(buyer_ids),
        )
        for buyer_id in buyer_ids:
            process_buyer_offers.delay(buyer_id)
        return {"dispatched": len(buyer_ids)}
    except Exception as exc:
        logger.exception("run_buyer_offer_processing: unexpected error - {}", exc)
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_buyer_offers(self, buyer_id: int):
    BuyerOfferService().run_for_buyer(buyer_id)

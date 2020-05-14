import time

from intergov.conf import env_queue_config
from intergov.repos.delivery_outbox import DeliveryOutboxRepo
from intergov.use_cases import DeliverCallbackUseCase

from intergov.loggers import logging

logger = logging.getLogger('callback_deliver')


class CallbacksDeliveryProcessor(object):
    """
    Iterate over the DeliverCallbackUseCase.
    """
    def _prepare_delivery_outbox_repo(self, conf):
        delivery_outbox_repo_conf = env_queue_config('PROC_DELIVERY_OUTBOX_REPO')
        if conf:
            delivery_outbox_repo_conf.update(conf)
        self.delivery_outbox_repo = DeliveryOutboxRepo(delivery_outbox_repo_conf)

    def _prepare_use_cases(self):
        self.uc = DeliverCallbackUseCase(
            delivery_outbox_repo=self.delivery_outbox_repo,
        )

    def __init__(self, delivery_outbox_repo_conf=None):
        self._prepare_delivery_outbox_repo(delivery_outbox_repo_conf)
        self._prepare_use_cases()

    def __iter__(self):
        logger.info("Starting the outbound callbacks deliverer")
        return self

    def __next__(self):
        try:
            result = self.uc.execute()
        except Exception as e:
            logger.exception(e)
            result = None
        return result


if __name__ == '__main__':  # pragma: no cover
    # To start it manually, from the base dir:
    # PYTHONPATH="`pwd`" python intergov/processors/callback_deliver/__init__.py
    for result in CallbacksDeliveryProcessor():
        # no message was processed, might not have been any, sleep
        # or the exception has been raised, sleep as well
        if result is None:
            time.sleep(1)

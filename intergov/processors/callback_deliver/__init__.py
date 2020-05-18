import time

from libtrustbridge.utils.loggers import logging
from libtrustbridge.utils.conf import env_queue_config
from libtrustbridge.websub.processors import Processor
from libtrustbridge.websub.repos import DeliveryOutboxRepo

from intergov.use_cases import DeliverCallbackUseCase

logger = logging.getLogger('callback_deliver')


def get_processor():
    delivery_outbox_repo_conf = env_queue_config('PROC_DELIVERY_OUTBOX_REPO')
    delivery_outbox_repo = DeliveryOutboxRepo(delivery_outbox_repo_conf)
    use_case = DeliverCallbackUseCase(
        delivery_outbox_repo=delivery_outbox_repo,
    )
    return Processor(use_case=use_case)


if __name__ == '__main__':  # pragma: no cover
    # To start it manually, from the base dir:
    # PYTHONPATH="`pwd`" python intergov/processors/callback_deliver/__init__.py
    for result in get_processor():
        # no message was processed, might not have been any, sleep
        # or the exception has been raised, sleep as well
        if result is None:
            time.sleep(1)

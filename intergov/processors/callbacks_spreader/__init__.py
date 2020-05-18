import time

from libtrustbridge.websub.repos import NotificationsRepo, DeliveryOutboxRepo, SubscriptionsRepo

from intergov.conf import env_s3_config, env_queue_config

from intergov.use_cases import (
    DispatchMessageToSubscribersUseCase,
)

from intergov.loggers import logging

logger = logging.getLogger('callbacks_spreader')


class CallbacksSpreaderProcessor(object):
    """
    Convert each incoming message to set of messages containing (websub_url, message)
    so they may be sent and fail separately
    """

    def _prepare_notifications_repo(self, conf):
        notifications_repo_conf = env_queue_config('PROC_OBJ_OUTBOX_REPO')
        if conf:
            notifications_repo_conf.update(conf)
        self.notifications_repo = NotificationsRepo(notifications_repo_conf)

    def _prepare_outbox_repo(self, conf):
        outbox_repo_conf = env_queue_config('PROC_DELIVERY_OUTBOX_REPO')
        if conf:
            outbox_repo_conf.update(conf)
        self.delivery_outbox_repo = DeliveryOutboxRepo(outbox_repo_conf)

    def _prepare_subscriptions_repo(self, conf):
        subscriptions_repo_conf = env_s3_config('PROC_SUB_REPO')
        if conf:
            subscriptions_repo_conf.update(conf)
        self.subscriptions_repo = SubscriptionsRepo(subscriptions_repo_conf)

    def _prepare_use_cases(self):
        self.uc = DispatchMessageToSubscribersUseCase(
            notifications_repo=self.notifications_repo,
            delivery_outbox_repo=self.delivery_outbox_repo,
            subscriptions_repo=self.subscriptions_repo,
        )

    def __init__(
        self,
        notifications_repo_conf=None,
        delivery_outbox_repo_conf=None,
        subscriptions_repo_conf=None
    ):
        self._prepare_notifications_repo(notifications_repo_conf)
        self._prepare_outbox_repo(delivery_outbox_repo_conf)
        self._prepare_subscriptions_repo(subscriptions_repo_conf)
        self._prepare_use_cases()

    def __iter__(self):
        logger.info("Starting the outbound callbacks processor")
        return self

    def __next__(self):
        try:
            result = self.uc.execute()
        except Exception as e:
            logger.exception(e)
            result = None
        return result


if __name__ == '__main__':   # pragma: no cover
    # To start it manually, from the base dir:
    # PYTHONPATH="`pwd`" python intergov/processors/callbacks_spreader/__init__.py
    for result in CallbacksSpreaderProcessor():
        if result is None:
            time.sleep(1)

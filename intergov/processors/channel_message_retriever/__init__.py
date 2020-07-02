import time

from libtrustbridge.utils.conf import env_queue_config

from intergov.loggers import logging
from intergov.processors.common.env import ROUTING_TABLE
from intergov.repos.bc_inbox.elasticmq.elasticmqrepo import BCInboxRepo
from intergov.repos.channel_notifications_inbox import ChannelNotificationRepo
from intergov.use_cases.process_channel_notifications import ProcessChannelNotificationUseCase

logger = logging.getLogger(__name__)


class ChannelMessageRetrieveProcessor:
    def __init__(self):
        channel_notification_repo_conf = env_queue_config('PROC_CHANNEL_NOTIFICATION_REPO')
        channel_notification_repo = ChannelNotificationRepo(channel_notification_repo_conf)

        bc_inbox_repo_conf = env_queue_config('PROC_BC_INBOX')
        bc_inbox_repo = BCInboxRepo(bc_inbox_repo_conf)
        self.use_case = ProcessChannelNotificationUseCase(
            channel_notification_repo=channel_notification_repo,
            bc_inbox_repo=bc_inbox_repo,
            routing_table=ROUTING_TABLE)

    def __iter__(self):
        logger.info("Starting the ChannelMessageRetrieveProcessor")
        return self

    def __next__(self):
        try:
            self.use_case.execute()
            return True
        except Exception as e:
            logger.exception(e)


if __name__ == '__main__':
    for result in ChannelMessageRetrieveProcessor():
        if result is None:
            time.sleep(1)

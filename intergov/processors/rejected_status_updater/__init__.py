import random
import time

from intergov.conf import env_s3_config, env_queue_config
from intergov.repos.message_lake import MessageLakeRepo
from intergov.repos.rejected_message import RejectedMessagesRepo
from intergov.use_cases import RejectPendingMessageUseCase

from intergov.loggers import logging

logger = logging.getLogger('rejected_status_updater')


class RejectedStatusUpdater(object):
    """
    Iterate over RejectPendingMessageUseCase
    """
    def __init__(self, rejected_message_repo_conf=None, message_lake_repo_conf=None):
        self._prepare_repos_confs(rejected_message_repo_conf, message_lake_repo_conf)
        self._prepare_repos()
        self._prepare_use_case()

    def _prepare_repos_confs(
        self,
        rejected_message_repo_conf=None,
        message_lake_repo_conf=None
    ):
        self.rejected_messages_repo_conf = env_queue_config('PROC_REJECTED_MESSAGES_REPO')
        self.message_lake_repo_conf = env_s3_config('PROC_MESSAGE_LAKE_REPO')
        if message_lake_repo_conf:
            self.message_lake_repo_conf.update(message_lake_repo_conf)
        if rejected_message_repo_conf:
            self.rejected_messages_repo_conf.update(rejected_message_repo_conf)

    def _prepare_repos(self):
        self.message_lake_repo = MessageLakeRepo(self.message_lake_repo_conf)
        self.rejected_messages_repo = RejectedMessagesRepo(self.rejected_messages_repo_conf)

    def _prepare_use_case(self):
        self.use_case = RejectPendingMessageUseCase(
            rejected_message_repo=self.rejected_messages_repo,
            message_lake_repo=self.message_lake_repo
        )

    def __iter__(self):
        logger.info("Starting the RejectedStatusUpdater")
        return self

    def __next__(self):
        try:
            result = self.use_case.execute()
        except Exception as e:
            logger.exception(e)
            result = None
        return result


if __name__ == '__main__':   # pragma: no cover
    # To start it manually, from the base dir:
    # PYTHONPATH="`pwd`" python intergov/processors/rejected_status_updater/__init__.py
    for result in RejectedStatusUpdater():
        if result is None:
            # better for tests
            time.sleep(random.randint(2, 20))

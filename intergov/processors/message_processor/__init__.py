import time

from intergov.repos.bc_inbox.elasticmq.elasticmqrepo import BCInboxRepo
from intergov.conf import env, env_s3_config, env_queue_config, env_postgres_config
from intergov.repos.api_outbox import ApiOutboxRepo
from intergov.repos.message_lake import MessageLakeRepo
from intergov.repos.object_acl import ObjectACLRepo
from intergov.repos.object_retrieval import ObjectRetrievalRepo
from intergov.repos.notifications import NotificationsRepo
from intergov.use_cases import ProcessMessageUseCase

from intergov.loggers import logging

logger = logging.getLogger('message_processor')


class InboundMessageProcessor(object):
    """
    Efficiently iterate over the ProcessMessageUseCase.
    """

    def _prepare_bc_inbox_repo(self, conf):
        bc_inbox_repo_conf = env_queue_config('PROC_BC_INBOX')
        if conf:
            bc_inbox_repo_conf.update(conf)
        self.bc_inbox_repo = BCInboxRepo(bc_inbox_repo_conf)

    def _prepare_message_lake_repo(self, conf):
        message_lake_repo_conf = env_s3_config('PROC_MESSAGE_LAKE')
        if conf:
            message_lake_repo_conf.update(conf)
        self.message_lake_repo = MessageLakeRepo(message_lake_repo_conf)

    def _prepare_object_acl_repo(self, conf):
        object_acl_repo_conf = env_s3_config('PROC_OBJECT_ACL_REPO')
        if conf:
            object_acl_repo_conf.update(conf)
        self.object_acl_repo = ObjectACLRepo(object_acl_repo_conf)

    def _prepare_object_retrieval_repo(self, conf):
        object_retrieval_repo_conf = env_queue_config('PROC_OBJ_RETR_REPO')
        if conf:
            object_retrieval_repo_conf.update(conf)
        self.object_retrieval_repo = ObjectRetrievalRepo(object_retrieval_repo_conf)

    def _prepare_notifications_repo(self, conf):
        notifications_repo_conf = env_queue_config('PROC_OBJ_OUTBOX_REPO')
        if conf:
            notifications_repo_conf.update(conf)
        self.notifications_repo = NotificationsRepo(notifications_repo_conf)

    def _prepare_blockchain_outbox_repo(self, conf):
        blockchain_outbox_repo_conf = env_postgres_config('PROC_BCH_OUTBOX_REPO')
        if conf:
            blockchain_outbox_repo_conf.update(conf)
        self.blockchain_outbox_repo = ApiOutboxRepo(blockchain_outbox_repo_conf)

    def _prepare_use_cases(self):
        self.uc = ProcessMessageUseCase(
            country=env('IGL_COUNTRY', default='AU'),
            bc_inbox_repo=self.bc_inbox_repo,
            message_lake_repo=self.message_lake_repo,
            object_acl_repo=self.object_acl_repo,
            object_retreval_repo=self.object_retrieval_repo,
            notifications_repo=self.notifications_repo,
            blockchain_outbox_repo=self.blockchain_outbox_repo,
        )

    def __init__(
        self,
        bc_inbox_repo_conf=None,
        message_lake_repo_conf=None,
        object_acl_repo_conf=None,
        object_retrieval_repo_conf=None,
        notifications_repo_conf=None,
        blockchain_outbox_repo_conf=None
    ):
        self._prepare_bc_inbox_repo(bc_inbox_repo_conf)
        self._prepare_message_lake_repo(message_lake_repo_conf)
        self._prepare_object_acl_repo(object_acl_repo_conf)
        self._prepare_object_retrieval_repo(object_retrieval_repo_conf)
        self._prepare_notifications_repo(notifications_repo_conf)
        self._prepare_blockchain_outbox_repo(blockchain_outbox_repo_conf)
        self._prepare_use_cases()

    def __iter__(self):
        logger.info("Starting the inbound message processor")
        return self

    def __next__(self):
        try:
            result = self.uc.execute()
        except Exception as e:
            logger.exception(e)
            result = None
        return result


if __name__ == '__main__':   # pragma: no cover
    for result in InboundMessageProcessor():
        if result is None:
            time.sleep(1)

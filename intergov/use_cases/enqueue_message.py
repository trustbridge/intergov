from intergov.loggers import logging
from intergov.monitoring import statsd_timer

logger = logging.getLogger(__name__)


class EnqueueMessageUseCase:
    """
    Used by the message_api(tx) and message_rx_api

    The message is received from:
        foreign source (blockchain or other)
        local source (exporter_app, chambers_app, etc)

    It already contains sender_ref value for both cases (set by a remote party
    or message_api for local messages)

    Quickly fires the message to message queue (SQS or elasticMQ)
    and exits, leaving real processing to the next layers and do not requiring
    api users to wait extra time.
    """

    def __init__(self, bc_inbox_repo):
        self.bc_inbox = bc_inbox_repo

    @statsd_timer("usecase.EnqueueMessageUseCase.execute")
    def execute(self, message):
        logger.info("Posting the message %s", message)
        if not message.is_valid():
            raise Exception("can't enqueue invalid message")
        if not message.sender_ref:
            raise Exception("received messages must have sender_ref")

        posted = self.bc_inbox.post(message)

        if not posted:
            return False
        return message

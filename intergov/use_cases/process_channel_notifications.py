import random
import uuid

from intergov.domain.wire_protocols.generic_discrete import Message
from intergov.loggers import logging
from intergov.repos.bc_inbox.elasticmq.elasticmqrepo import BCInboxRepo
from intergov.repos.channel_notifications_inbox import ChannelNotificationRepo
from intergov.use_cases import EnqueueMessageUseCase
from intergov.use_cases.request_channel_api import RequestChannelAPIUseCase, ChannelApiFailure
from intergov.use_cases.route_to_channel import get_channel_by_id

logger = logging.getLogger()


class ChannelNotFound(Exception):
    pass


class ChannelNotificationUseCase:
    CHANNEL_API_GET_MESSAGE_ENDPOINT = 'messages'
    CHANNEL_ID = 'channel_id'
    NOTIFICATION_PAYLOAD = 'notification_payload'
    ATTEMPT = 'attempt'

    def __init__(self, channel_notification_repo: ChannelNotificationRepo):
        self.channel_notification_repo = channel_notification_repo


class EnqueueChannelNotificationUseCase(ChannelNotificationUseCase):
    def execute(self, channel, notification_payload):
        """Enqueue job for further processing (processor calls execute() method)"""
        job_payload = {
            self.CHANNEL_ID: channel['Id'],
            self.NOTIFICATION_PAYLOAD: notification_payload,
            self.ATTEMPT: 1
        }
        self._post(job_payload)

    def retry(self, job_payload, attempt):
        job_payload[self.ATTEMPT] = attempt
        self._post(job_payload, delay=self._get_retry_time(attempt))

    def _post(self, job_payload, delay=0):
        self.channel_notification_repo.post_job(job_payload, delay_seconds=delay)

    @staticmethod
    def _get_retry_time(attempt):
        """exponential back off with jitter"""
        if attempt == 1:
            return 0
        base = 8
        max_retry = 100
        delay = min(base * 2 ** attempt, max_retry)
        jitter = random.uniform(0, delay / 2)
        return int(delay / 2 + jitter)


class ProcessChannelNotificationUseCase(ChannelNotificationUseCase):
    MAX_ATTEMPTS = 3

    def __init__(self, channel_notification_repo: ChannelNotificationRepo, bc_inbox_repo: BCInboxRepo, routing_table):
        super().__init__(channel_notification_repo)
        self.routing_table = routing_table
        self.enqueue_message_use_case = EnqueueMessageUseCase(bc_inbox_repo)

    def execute(self):
        """
        Get message from channel API and post it to message API.
        Retry in case of failure
        """

        job = self.channel_notification_repo.get_job()
        if not job:
            return

        queue_message_id, job_payload = job
        attempt = job_payload[self.ATTEMPT]

        try:
            self.process(job_payload)
        except ChannelApiFailure as e:
            logger.info("%s: processing channel notification failure", queue_message_id)
            logger.exception(e)
            if attempt < self.MAX_ATTEMPTS:
                attempt += 1
                EnqueueChannelNotificationUseCase(self.channel_notification_repo).retry(job_payload, attempt)
                self.channel_notification_repo.delete(queue_message_id)
                return
            raise
        else:
            self.channel_notification_repo.delete(queue_message_id)

    def process(self, job_payload):
        logger.debug("Processing job: %r", job_payload)
        channel_id = job_payload[self.CHANNEL_ID]
        channel = get_channel_by_id(channel_id, self.routing_table)
        if not channel:
            raise ChannelNotFound("Channel not found, id: %s" % channel_id)

        notification_payload = job_payload[self.NOTIFICATION_PAYLOAD]
        message = self._get_message(channel, notification_payload['id'])
        self.enqueue_message_use_case.execute(message)

    def _get_message(self, channel, message_id):
        request_channel_use_case = RequestChannelAPIUseCase(channel)
        message_payload = request_channel_use_case.get_message(message_id)
        message = Message.from_dict(message_payload['message'])
        message.status = "received"
        message.sender_ref = str(uuid.uuid4())
        return message

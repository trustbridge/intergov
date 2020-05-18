import random
import requests

from libtrustbridge.utils.loggers import logging  # NOQA
from libtrustbridge.websub import repos

from intergov.monitoring import statsd_timer

logger = logging.getLogger(__name__)


class DeliverCallbackUseCase:
    """
    Is used by a callback deliverer worker

    Reads queue delivery_outbox_repo consisting of tasks in format:
        (url, message)

    Then such message should be either sent to this URL and the task is deleted
    or, in case of any error, not to be deleted and to be tried again
    (up to MAX_RETRIES times)

    TODO: rate limits, no more than 100 messages to a single url per 10 seconds?
    """

    MAX_RETRIES = 2

    def __init__(self, delivery_outbox_repo: repos.DeliveryOutboxRepo):
        self.delivery_outbox = delivery_outbox_repo

    def execute(self):
        deliverable = self.delivery_outbox.get_job()
        if not deliverable:
            return None
        else:
            (queue_msg_id, job) = deliverable
        return self.process(queue_msg_id, job)

    @statsd_timer("usecase.DeliverCallbackUseCase.process")
    def process(self, queue_msg_id, job):
        # TODO: test to ensure this message has a callback_url
        subscribe_url = job['s']
        payload = job.get('payload')

        retry_number = int(job.get('retry', 0))
        # second line of defence. Just in case

        if retry_number > self.MAX_RETRIES:
            logger.error(
                "Dropping notification %s about %s due to max retries reached",
                subscribe_url,
                payload
            )
            self.delivery_outbox.delete(queue_msg_id)
            return False

        try:
            is_delivered = self._deliver_notification(
                subscribe_url, payload
            )
        except Exception as e:
            logger.exception(e)
            is_delivered = False

        # we always delete a message, because we want to re-send it with
        # retries count increased
        deleted = self.delivery_outbox.delete(queue_msg_id)
        if not deleted:
            # quite strange, may be the same message is being processed twice
            # or it's already exhausted it's retry count on the
            # queue broker side
            logger.error(
                "Unable to delete message %s from the delivery_outbox",
                queue_msg_id
            )
            return False

        if not is_delivered:
            # @Neketek: I think it's better to not post the job at all instead of filtering it
            if retry_number + 1 > self.MAX_RETRIES:
                logger.error(
                    "Dropping notification %s about %s due to max retries reached",
                    subscribe_url,
                    payload
                )
                return False
            logger.info("Delivery failed, re-schedule it")
            self.delivery_outbox.post_job(
                {
                    's': subscribe_url,
                    'payload': payload,
                    'retry': retry_number + 1
                },
                # put it to the end of queue and with some nice delay
                # TODO: delay = retry_number * 30 + random.randint(0, 100)
                # for real cases (it's too slow for development)
                delay_seconds=random.randint(1, 10)
            )
            return False

        return True

    def _deliver_notification(self, url, payload):
        # https://indieweb.org/How_to_publish_and_consume_WebSub
        # https://www.w3.org/TR/websub/#x7-content-distribution
        # TODO: respect Retry-After header from the receiver
        # TODO: move to env variable, is unlikely to be used anyway
        hub_url = "127.0.0.1:5102"

        logger.info(
            "Sending WebSub payload \n    %s to callback URL \n    %s",
            payload, url
        )
        resp = requests.post(
            url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'Link': '<https://{}/>; rel="hub"'.format(
                    hub_url,
                ),
            }
        )

        if str(resp.status_code).startswith('2'):
            return True
        else:
            logger.error(
                "Subscription url %s seems to be invalid, returns %s",
                url,
                resp.status_code
            )
            logger.error(resp.text)
            return False

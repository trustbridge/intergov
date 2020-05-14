import json

from intergov.loggers import logging
from intergov.monitoring import statsd_timer
from intergov.serializers import generic_discrete_message as ser

logger = logging.getLogger(__name__)


class DispatchMessageToSubscribersUseCase:
    """
    Used by the callbacks spreader worker.

    This is the "fan-out" part of the WebSub,
    where each event dispatched
    to all the relevant subscribers.
    For each event (notification),
    it looks-up the relevant subscribers
    and dispatches a callback task
    so that they will be notified.

    There is a downstream delivery processor
    that actually makes the callback,
    it is insulated from this process
    by the delivery outbox message queue.

    Note: In this application
    the subscription signature
    is based on the message predicate.
    """

    def __init__(
            self, notifications_repo,
            delivery_outbox_repo, subscriptions_repo):
        self.notifications = notifications_repo
        self.delivery_outbox = delivery_outbox_repo
        self.subscriptions = subscriptions_repo

    def execute(self):
        fetched_publish = self.notifications.get_job()
        if not fetched_publish:
            return None
        (publish_msg_id, message_job) = fetched_publish
        return self.process(publish_msg_id, message_job)

    @statsd_timer("usecase.DispatchMessageToSubscribersUseCase.process")
    def process(self, publish_msg_id, message_job):
        # message_job is either a Message class
        # or a dict with 'message' field which is Message
        # which may be empty
        # or just a dict which must be sent as a callback directly
        message = message_job.get('message')
        if isinstance(message_job, dict) and "topic" in message_job:
            topic = message_job["topic"]
            assert topic
            predicate = None
        else:
            predicate = message_job.get('predicate') or message.predicate
            assert predicate
            topic = None

        # not both at once
        assert bool(predicate) != bool(topic)

        # find the subscribers for this predicate
        subscribers = self._get_subscribers(predicate or topic)

        # what is worse, multiple delivery or lost messages?
        # here we assume lost messages are worse
        # given the delivery outbox is just a queue there aren't many reasons
        # for it to fail, real fails will be on the next step - when it's trivial
        # to re-process the single message when other ones will be fine.
        # (see DeliverCallbackUseCase)
        all_OK = True

        payload = {}
        if message:
            payload = json.dumps(message, cls=ser.MessageJSONEncoder)
        else:
            payload = message_job

        for s in subscribers:
            job = {
                's': s,  # subscribed callback url
                'payload': payload  # the payload to be sent to the callback
            }
            logger.info("Scheduling notification of \n[%s] with payload \n%s", s, payload)
            status = self.delivery_outbox.post_job(job)
            if not status:
                all_OK = False

        if all_OK:
            self.notifications.delete(publish_msg_id)
            return True
        else:
            return False

    def _get_subscribers(self, predicate_or_topic):
        subscribers = self.subscriptions.search(predicate_or_topic, layered=True)
        if not subscribers:
            logger.info("Nobody to notify about the %s", predicate_or_topic)
        return subscribers

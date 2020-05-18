import json

from libtrustbridge.websub import repos

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
            self, notifications_repo: repos.NotificationsRepo,
            delivery_outbox_repo: repos.DeliveryOutboxRepo,
            subscriptions_repo: repos.SubscriptionsRepo):
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
        predicate = message_job.get('predicate') or message.predicate
        assert predicate

        # find the subscribers for this predicate
        subscribers = self._get_subscribers(predicate)

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
            if not s.is_valid:
                continue
            job = {
                's': s.callback_url,  # subscribed callback url
                'payload': payload  # the payload to be sent to the callback
            }
            logger.info("Scheduling notification of \n[%s] with payload \n%s", s.callback_url, payload)
            status = self.delivery_outbox.post_job(job)
            if not status:
                all_OK = False

        if all_OK:
            self.notifications.delete(publish_msg_id)
            return True
        else:
            return False

    def _get_subscribers(self, predicate):
        pattern = repos.Pattern(predicate)
        subscribers = self.subscriptions.get_subscriptions_by_pattern(pattern)
        if not subscribers:
            logger.info("Nobody to notify about the message %s", predicate)
        return subscribers

import datetime
from time import sleep
from urllib.parse import urljoin

from intergov.loggers import logging
from intergov.processors.common import env
from intergov.processors.common.utils import get_channels_to_subscribe_as
from intergov.use_cases.request_channel_api import (
    RequestChannelAPIUseCase, SubscriptionFailure, InvalidSubscriptionParameters
)

logger = logging.getLogger(__name__)


class SubscriptionHandler:
    CHANNEL_API_SUBSCRIBE_ENDPOINT = '/messages/subscriptions/by_jurisdiction'

    def __init__(self):
        self.last_subscribed_at = None
        self.subscription_period = datetime.timedelta(minutes=60)

    def run(self):
        for channel in get_channels_to_subscribe_as(env.ROUTING_TABLE, env.JURISDICTION):
            if self.should_update_subscription():
                logger.info("Subscribing to channel %s", channel["Name"])
                try:
                    self.subscribe(channel)
                except Exception as e:
                    logger.error("Unable to subscribe to channel %s - %s", channel, str(e))

    def should_update_subscription(self):
        now = datetime.datetime.utcnow()
        return not (self.last_subscribed_at and (now - self.last_subscribed_at < self.subscription_period / 2))

    def subscribe(self, channel):
        channel_url = self.get_channel_subscribe_endpoint_url(channel)
        now = datetime.datetime.utcnow()
        try:
            callback_url = self.get_callback_url(channel)
            logger.info('Sending subscription request to %s', channel_url)
            RequestChannelAPIUseCase(channel).subscribe_by_jurisdiction(callback_url, env.JURISDICTION)
        except (SubscriptionFailure, InvalidSubscriptionParameters) as e:
            logger.error(e)
        else:
            self.last_subscribed_at = now
            logger.info('Successfully subscribed at %s' % self.last_subscribed_at)

    @staticmethod
    def get_callback_url(channel):
        return urljoin(env.MESSAGE_RX_API_URL, 'channel-message/{Id}'.format(**channel))

    def get_channel_subscribe_endpoint_url(self, channel):
        return urljoin(channel['ChannelUrl'], self.CHANNEL_API_SUBSCRIBE_ENDPOINT)


if __name__ == '__main__':
    processor = SubscriptionHandler()
    sleep_period = 30
    while True:
        processor.run()
        sleep(sleep_period)

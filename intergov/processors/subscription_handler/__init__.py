import datetime
from time import sleep

from intergov.loggers import logging
from intergov.processors.common import env
from intergov.processors.common.utils import get_channels_for_local_jurisdiction
from intergov.use_cases import SubscribeByJurisdictionUseCase
from intergov.use_cases.subscribe_by_jurisdiction import SubscriptionFailure, InvalidSubscriptionParameters

logger = logging.getLogger(__name__)


class SubscriptionHandler:
    def __init__(self):
        self.last_subscribed_at = None
        self.subscription_period = datetime.timedelta(days=1)

    def run(self):
        for channel in get_channels_for_local_jurisdiction(env.ROUTING_TABLE, env.COUNTRY):
            if self.should_update_subscription():
                self.subscribe(channel)

    def should_update_subscription(self):
        now = datetime.datetime.utcnow()

        return not (self.last_subscribed_at and now - self.last_subscribed_at < self.subscription_period)

    def subscribe(self, channel):
        channel_url = channel['ChannelUrl']
        now = datetime.datetime.utcnow()
        try:
            callback_url = self.get_callback_url(channel)
            logger.info('Sending subscription request to %s', channel_url)
            SubscribeByJurisdictionUseCase(channel_url, callback_url, env.COUNTRY).subscribe()
        except (SubscriptionFailure, InvalidSubscriptionParameters) as e:
            logger.error(e)
        else:
            self.last_subscribed_at = now
            logger.info('Successfully subscribed at %s' % self.last_subscribed_at)

    @staticmethod
    def get_callback_url(channel):
        return '{base_url}/channel-message/{Id}'.format(base_url=env.MESSAGE_RX_API_URL, **channel)


if __name__ == '__main__':
    while True:
        SubscriptionHandler().run()
        sleep(60)

from intergov.loggers import logging
from datetime import datetime, timedelta
from time import sleep

from intergov.processors.common import env
from intergov.processors.common.utils import get_channels_for_local_jurisdiction
from intergov.use_cases import SubscribeByJurisdictionUseCase
from intergov.use_cases.subscribe_by_jurisdiction import SubscriptionFailure, InvalidSubscriptionParameters

logger = logging.getLogger(__name__)


class SubscriptionHandler:
    def __init__(self):
        self.last_subscribed_at = None
        self.subscription_period = timedelta(days=1)

    def run(self):
        for channel in get_channels_for_local_jurisdiction(env.ROUTING_TABLE, env.COUNTRY):
            if self.should_update_subscription():
                self.subscribe(channel['ChannelUrl'])

    def should_update_subscription(self):
        now = datetime.utcnow()

        return not (self.last_subscribed_at and now - self.last_subscribed_at < self.subscription_period)

    def subscribe(self, channel_url):
        now = datetime.utcnow()
        try:
            callback_url = '%s/channel-message' % env.MESSAGE_RX_API_URL
            logger.info('Sending subscription request to %s', channel_url)
            SubscribeByJurisdictionUseCase(channel_url, callback_url, env.COUNTRY).subscribe()
        except (SubscriptionFailure, InvalidSubscriptionParameters) as e:
            logger.error(e)
        else:
            self.last_subscribed_at = now
            logger.info('Successfully subscribed at %s' % self.last_subscribed_at)


if __name__ == '__main__':
    while True:
        SubscriptionHandler().run()
        sleep(60)

import logging
from datetime import datetime, timedelta
from time import sleep

from intergov.processors.common import env
from intergov.use_cases import SubscribeByJurisdictionUseCase
from intergov.use_cases.subscribe_by_jurisdiction import SubscriptionFailure, InvalidSubscriptionParameters

logger = logging.getLogger(__name__)


class SubscriptionHandler:
    def __init__(self):
        self.last_subscribed_at = None
        self.subscription_period = timedelta(days=1)

    def run(self):
        while True:
            if self.should_update_subscription():
                self.subscribe()

            sleep(60)

    def should_update_subscription(self):
        now = datetime.utcnow()

        return not (self.last_subscribed_at and now - self.last_subscribed_at < self.subscription_period)

    def subscribe(self):
        now = datetime.utcnow()
        try:
            channel_api_url = env.CHANNEL_SUBSCRIBE_URL
            callback_url = '%s/channel-message' % env.MESSAGE_RX_API_URL
            logger.info('Sending subscription request to %s', channel_api_url)
            SubscribeByJurisdictionUseCase(channel_api_url, callback_url, env.COUNTRY).subscribe()
        except (SubscriptionFailure, InvalidSubscriptionParameters) as e:
            logger.error(e)
        else:
            self.last_subscribed_at = now
            logger.info('Successfully subscribed at %s' % self.last_subscribed_at)


if __name__ == '__main__':
    SubscriptionHandler().run()

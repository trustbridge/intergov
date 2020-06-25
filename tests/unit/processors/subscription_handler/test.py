from unittest import mock

import pytest
import responses
from freezegun import freeze_time

from intergov.processors.subscription_handler import SubscriptionHandler


@pytest.mark.usefixtures("mocked_responses")
class TestSubscriptionHandler:
    @pytest.fixture(autouse=True)
    def mocked_processors_common_env(self):
        with mock.patch('intergov.processors.subscription_handler.env') as mocked_env:
            self.env = mocked_env
            self.env.MESSAGE_RX_API_URL = 'http://mock_message_rx_api'
            self.env.COUNTRY = 'AU'
            self.env.CHANNEL_SUBSCRIBE_URL = 'https://shared-db-channel-api:81/messages/subscriptions/by_jurisdiction'
            yield

    def test_should_update_subscription__for_initial_call__should_return_true(self):
        handler = SubscriptionHandler()
        assert handler.should_update_subscription() is True

    def test_should_update_subscription__after_successful_subscription__should_return_false(self):
        self.mocked_responses.add(responses.POST, self.env.CHANNEL_SUBSCRIBE_URL, status=202)
        handler = SubscriptionHandler()
        handler.subscribe()
        assert handler.should_update_subscription() is False

        expected_body = ('hub.mode=subscribe&'
                         'hub.callback=http%3A%2F%2Fmock_message_rx_api%2Fchannel-message&'
                         'hub.topic=AU&'
                         'hub.secret=')
        assert self.mocked_responses.calls[0].request.body == expected_body

    def test_should_update_subscription__in_1_day_after_successful_subscription__should_return_true(self):
        self.mocked_responses.add(responses.POST, self.env.CHANNEL_SUBSCRIBE_URL, status=202)
        handler = SubscriptionHandler()
        with freeze_time('2020-06-25 11:26:00'):
            handler.subscribe()
        with freeze_time('2020-06-26 11:26:00'):
            assert handler.should_update_subscription() is True

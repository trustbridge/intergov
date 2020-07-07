from unittest import mock
from urllib.parse import urlencode

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
            self.channel_subscribe_url = "https://sharedchannel.services.devnet.trustbridge.io/messages/subscriptions/by_jurisdiction"
            self.env.ROUTING_TABLE = [
                {
                    "Id": "1",
                    "Jurisdiction": "AU",
                    "Name": "to AU",
                    "ChannelUrl": "https://sharedchannel.services.devnet.trustbridge.io/",
                    "ChannelAuth": "None"
                },
                {
                    "Id": "2",
                    "Jurisdiction": "SG",
                    "Name": "to SG",
                    "ChannelUrl": "https://sharedchannel.services.devnet.trustbridge.io/",
                    "ChannelAuth": "None"
                },
                {
                    "Id": "3",
                    "Jurisdiction": "FR",
                    "Name": "to FR",
                    "ChannelUrl": "http://docker-host:7500/",
                    "ChannelAuth": "None"
                }
            ]

            yield

    def test_should_update_subscription__for_initial_call__should_return_true(self):
        handler = SubscriptionHandler()
        assert handler.should_update_subscription() is True

    def test_should_update_subscription__after_successful_subscription__should_return_false(self):
        self.mocked_responses.add(responses.POST, self.channel_subscribe_url, status=202)
        handler = SubscriptionHandler()
        handler.run()
        assert handler.should_update_subscription() is False

        expected_body = urlencode(
            {
                'hub.mode': 'subscribe',
                'hub.callback': 'http://mock_message_rx_api/channel-message/1',
                'hub.topic': 'AU',
                'hub.secret': '',
            })
        assert self.mocked_responses.calls[0].request.body == expected_body

    def test_should_update_subscription__in_1_day_after_successful_subscription__should_return_true(self):
        self.mocked_responses.add(responses.POST, self.channel_subscribe_url, status=202)
        handler = SubscriptionHandler()
        with freeze_time('2020-06-25 11:26:00'):
            handler.run()
        with freeze_time('2020-06-26 11:26:00'):
            assert handler.should_update_subscription() is True

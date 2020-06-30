import pytest
import responses

from intergov.use_cases.subscribe_by_jurisdiction import (
    SubscribeByJurisdictionUseCase, SubscriptionFailure, InvalidSubscriptionParameters
)


@pytest.mark.usefixtures("mocked_responses")
class TestSubscribeByJurisdictionUseCase:
    def test_use_case__with_missing_params__should_raise_exception(self):
        with pytest.raises(InvalidSubscriptionParameters):
            SubscribeByJurisdictionUseCase(channel_api_url='', callback_url='something', igl_country='something')
        with pytest.raises(InvalidSubscriptionParameters):
            SubscribeByJurisdictionUseCase(channel_api_url='something', callback_url='', igl_country='something')
        with pytest.raises(InvalidSubscriptionParameters):
            SubscribeByJurisdictionUseCase(channel_api_url='something', callback_url='something', igl_country='')

    def test_use_case__when_channel_response_not_ok__should_raise_exception(self):
        channel_api_url = 'http://channel_api_url:8000/message/subscription/by_jurisdiction'
        self.mocked_responses.add(responses.POST, channel_api_url, status=400)
        with pytest.raises(SubscriptionFailure):
            SubscribeByJurisdictionUseCase(
                channel_api_url=channel_api_url,
                callback_url='https://callback.url', igl_country='AU', secret='123').subscribe()

    def test_use_case__happy_path(self):
        channel_api_url = 'http://channel_api_url:8000/message/subscription/by_jurisdiction'
        self.mocked_responses.add(responses.POST, channel_api_url, status=202)
        SubscribeByJurisdictionUseCase(
            channel_api_url=channel_api_url,
            callback_url='https://callback.url', igl_country='AU', secret='123').subscribe()

        body = ('hub.mode=subscribe&'
                'hub.callback=https%3A%2F%2Fcallback.url&'
                'hub.topic=AU&'
                'hub.secret=123')
        assert self.mocked_responses.calls[0].request.body == body

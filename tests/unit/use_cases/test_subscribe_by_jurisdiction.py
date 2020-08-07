import pytest
import responses

from intergov.use_cases.request_channel_api import (
    RequestChannelAPIUseCase, InvalidSubscriptionParameters, SubscriptionFailure
)


@pytest.mark.usefixtures("mocked_responses")
class TestSubscribeByJurisdiction:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.channel_config = {
            "Id": "1234",
            "Name": "shared db channel to Australia",
            "Jurisdiction": "AU",
            "Predicate": "UN.CEFACT.",
            "ChannelUrl": "http://channel_api_url:8000",
        }
        self.channel_api_url = 'http://channel_api_url:8000/messages/subscriptions/by_jurisdiction'
        self.use_case = RequestChannelAPIUseCase(
            channel_config=self.channel_config
        )

    def test_use_case__with_missing_params__should_raise_exception(self):
        with pytest.raises(InvalidSubscriptionParameters):
            self.use_case.subscribe_by_jurisdiction(callback_url='', jurisdiction='something')
        with pytest.raises(InvalidSubscriptionParameters):
            self.use_case.subscribe_by_jurisdiction(callback_url='something', jurisdiction='')

    def test_use_case__when_channel_response_not_ok__should_raise_exception(self):
        self.mocked_responses.add(responses.POST, self.channel_api_url, status=400)
        with pytest.raises(SubscriptionFailure):
            response = self.use_case.subscribe_by_jurisdiction(callback_url='https://callback.url', jurisdiction='AU', secret='123')
            response.raise_for_status()

    def test_use_case__happy_path(self):
        self.mocked_responses.add(responses.POST, self.channel_api_url, status=202)
        self.use_case.subscribe_by_jurisdiction(callback_url='https://callback.url', jurisdiction='AU', secret='123')

        body = ('hub.mode=subscribe&'
                'hub.callback=https%3A%2F%2Fcallback.url&'
                'hub.topic=AU&'
                'hub.secret=123')
        assert self.mocked_responses.calls[0].request.body == body

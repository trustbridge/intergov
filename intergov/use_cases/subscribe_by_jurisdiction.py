import requests


class SubscriptionFailure(Exception):
    pass


class InvalidSubscriptionParameters(Exception):
    pass


class SubscribeByJurisdictionUseCase:
    def __init__(self, channel_api_url, callback_url, igl_country, secret=''):
        if not (channel_api_url and callback_url and igl_country):
            raise InvalidSubscriptionParameters
        self.channel_api_url = channel_api_url
        self.callback_url = callback_url
        self.igl_country = igl_country
        self.secret = secret

    def subscribe(self):
        params = {
            'hub.mode': 'subscribe',
            'hub.callback': self.callback_url,
            'hub.topic': self.igl_country,
            'hub.secret': self.secret
        }
        response = requests.post(self.channel_api_url, params)

        if response.status_code != 202:
            raise SubscriptionFailure

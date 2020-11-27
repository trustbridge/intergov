from urllib.parse import urljoin

import requests

from intergov.loggers import logging
from intergov.use_cases.common import BaseUseCase
from intergov.use_cases.get_cognito_auth import GetCognitoAuthUseCase

logger = logging.getLogger()


class InvalidSubscriptionParameters(Exception):
    pass


class ChannelApiFailure(Exception):
    pass


class SubscriptionFailure(ChannelApiFailure):
    pass


class RequestChannelAPIUseCase(BaseUseCase):
    CHANNEL_API_GET_MESSAGE_ENDPOINT = '/messages'
    CHANNEL_API_SUBSCRIBE_BY_JURISDICTION_ENDPOINT = '/messages/subscriptions/by_jurisdiction'

    def __init__(self, channel_config):
        self.config = channel_config
        self.auth_use_case = None

        if self.config.get("ChannelAuth") == "Cognito/JWT":
            self.auth_use_case = GetCognitoAuthUseCase(**self.config["ChannelAuthDetails"])

    def get_message(self, message_id):
        endpoint = '%s/%s' % (self.CHANNEL_API_GET_MESSAGE_ENDPOINT, message_id)
        response = self.get(endpoint)
        if response.status_code != 200:
            raise ChannelApiFailure("Could not get message from Channel API, response:%s" % response)
        return response.json()

    def subscribe_by_jurisdiction(self, callback_url, jurisdiction, secret=''):
        if not (callback_url and jurisdiction):
            raise InvalidSubscriptionParameters
        params = {
            'hub.mode': 'subscribe',
            'hub.callback': callback_url,
            'hub.topic': jurisdiction,
            'hub.secret': secret
        }
        endpoint = self.CHANNEL_API_SUBSCRIBE_BY_JURISDICTION_ENDPOINT
        response = self.post(endpoint, data=params)
        if response.status_code not in (200, 202):
            logger.error(
                "Non-202 or 200 response from a channel %s, %s", endpoint, str(response.content)
            )
            raise SubscriptionFailure("Non-200 or 202 response from a channel")

    def get(self, endpoint):
        url = self.get_url(endpoint)
        return requests.get(url, headers=self.get_headers())

    def post(self, endpoint, data=None, json=None):
        url = self.get_url(endpoint)
        logger.debug('Sending POST to %s, data: %r, json: %s', url, data, json)
        return requests.post(url, data=data, json=json, headers=self.get_headers())

    def get_headers(self):
        headers = {}
        if self.auth_use_case:
            token = self.auth_use_case.get_jwt()
            headers["Authorization"] = f"Bearer {token}"

        headers.update(**headers)
        return headers

    def get_url(self, endpoint):
        return urljoin(self.config['ChannelUrl'], endpoint)

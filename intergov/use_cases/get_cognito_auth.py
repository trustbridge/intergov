import base64
import datetime

import requests

from intergov.loggers import logging

logger = logging.getLogger(__name__)


class GetCognitoAuthInitError(Exception):
    pass


class GetCognitoAuthUseCase:
    def __init__(self, client_id, client_secret, scope, token_endpoint):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.token_endpoint = token_endpoint

        self._jwt = None
        self._jwt_expires_at = None

        if not client_id or not client_secret:
            raise GetCognitoAuthInitError('client_id and client_secret are required')

    def get_jwt(self):
        """return cached jwt token, when expired issue new one"""
        now = datetime.datetime.utcnow()
        if self._jwt_expires_at and self._jwt_expires_at < now:
            self._jwt = None

        if self._jwt:
            return self._jwt

        return self._issue_cognito_jwt()

    def _issue_cognito_jwt(self):
        now = datetime.datetime.utcnow()

        cognito_auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode("utf-8")

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "scope": self.scope,
        }
        headers = {
            'Authorization': f'Basic {cognito_auth}',
        }
        token_resp = requests.post(self.token_endpoint, data=data, headers=headers)

        token_resp.raise_for_status()
        json_resp = token_resp.json()
        logger.info("Retrieved new JWT expires in %s", json_resp['expires_in'])

        self._jwt = json_resp["access_token"]
        seconds_to_renew = self._get_seconds_to_renew(json_resp['expires_in'])
        self._jwt_expires_at = now + datetime.timedelta(seconds=seconds_to_renew)
        return self._jwt

    def _get_seconds_to_renew(self, expires_in):
        if expires_in < 60:
            return int(expires_in / 2)

        return expires_in - 60

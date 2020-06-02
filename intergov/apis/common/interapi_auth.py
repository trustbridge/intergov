import binascii
import base64
import datetime
from functools import lru_cache

import requests

from intergov.loggers import logging

logger = logging.getLogger(__name__)


class AuthMixin:
    """
    In the general use-case our APIs should use some auth talking to other
    APIs, so we need to retrieve correct credentials based on env variables
    configuration
    """

    def _get_auth_headers(self, auth_method, auth_parameters=None):
        # for auth_method "none" there are no auth_parameters read
        # for auth_method Cognito/JWT it must be a dict of format:
        #  {"client_id": "1", "client_secret": "2", "scopes": "3", "wellknown_url": "4"}
        if auth_method == "none":
            # no auth - local/test setups
            return {}
        elif auth_method == "Cognito/JWT":
            assert auth_parameters, "auth_parameters must be configured correctly"
            assert "client_id" in auth_parameters, "auth_parameters must be configured correctly"
            assert "client_secret" in auth_parameters, "auth_parameters must be configured correctly"
            return {
                "Authorization": "Bearer " + self._get_cached_cognito_jwt(
                    auth_parameters
                )
            }
        else:
            raise Exception(
                f"Improperly configured: "
                f"unsupported auth mechanism {auth_method}"
            )

    def _get_cached_cognito_jwt(self, auth_parameters):
        """
        This is implementation-specific procedure. Good thing - it's useful
        and will be used for our test installations.
        Bad thing - it's really cognito-specific. In fact it could be easily
        changed to generic OIDC IDP.
        Good thing - it could be moved to a subclass easily, preserving the core
        intergov pureness
        """
        cache_key = str(binascii.crc32(str(auth_parameters).encode("utf-8")))
        old_token_exp = getattr(self, f"_cognito_jwt_expiration_date_{cache_key}", None)
        old_token_value = getattr(self, f"_cognito_jwt_{cache_key}", None)

        if old_token_exp and old_token_exp < datetime.datetime.utcnow():
            old_token_value = None

        if old_token_value:
            # cache hit
            return old_token_value

        new_token, expires = self._issue_cognito_jwt(auth_parameters)
        setattr(
            self,
            f"_cognito_jwt_{cache_key}",
            new_token
        )
        if expires < 60:
            seconds_to_renew = int(expires / 2)
        else:
            seconds_to_renew = expires - 60
        setattr(
            self,
            f'_cognito_jwt_expiration_date_{cache_key}',
            (
                datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds_to_renew)
            )
        )
        return new_token

    def _issue_cognito_jwt(self, auth_parameters):
        # see _get_cached_cognito_jwt descr about the design concerns
        OAUTH_CLIENT_ID = auth_parameters["client_id"]
        OAUTH_CLIENT_SECRET = auth_parameters["client_secret"]
        OAUTH_SCOPES = auth_parameters["scopes"]

        cognito_auth = base64.b64encode(
            f"{OAUTH_CLIENT_ID}:{OAUTH_CLIENT_SECRET}".encode("utf-8")
        ).decode("utf-8")
        token_resp = requests.post(
            auth_parameters.get("token_endpoint") or _oidc_token_url(auth_parameters["wellknown_url"]),
            data={
                "grant_type": "client_credentials",
                "client_id": OAUTH_CLIENT_ID,
                "scope": OAUTH_SCOPES,
            },
            headers={
                'Authorization': f'Basic {cognito_auth}',
            }
        )
        assert token_resp.status_code == 200, token_resp.json()
        json_resp = token_resp.json()
        logger.info(
            "The new JWT for %s ends in %s",
            auth_parameters["client_id"],
            json_resp['expires_in']
        )
        return json_resp["access_token"], json_resp['expires_in']


@lru_cache(maxsize=2)  # it's fine to cache for a long time
def _oidc_token_url(wellknown_url):
    # see _get_cached_cognito_jwt descr about the design concerns
    wellknown_content = requests.get(wellknown_url)
    assert wellknown_content.status_code == 200
    return wellknown_content.json().get("token_endpoint")

import base64
import datetime
from functools import lru_cache

import requests

from intergov.conf import env
from intergov.loggers import logging

logger = logging.getLogger(__name__)


class HttpApiChannel:
    """
    Channel relying on some HTTP api available without further information
    about underlying messages carried (which could be anything from blockchain
    to email messages)

    Example of the API must be provided on this endpoint:
    https://github.com/trustbridge/shared-db-channel/blob/master/swagger.yaml

    In fact just sending the payload to these urls and subscribing to results

    Please note the channel class tend to be static during the whole
    worker functioning (implementation detail), so it could cache values in itself
    """

    ID = 'HttpApiChannel'

    def __init__(self, config):
        self.CONFIG = config.copy()
        assert self.CONFIG.get("ChannelUrl"), "Lack of required parameter in the config"
        assert self.CONFIG.get("ChannelAuth"), "Lack of required parameter in the config"
        if self.CONFIG['ChannelUrl'].endswith("/"):
            self.CONFIG['ChannelUrl'] = self.CONFIG['ChannelUrl'][:-1]

    def __str__(self):
        return f"HttpApiChannel({self.CONFIG['ChannelUrl']})"

    def screen_message(self, message):
        # there is no rules to screen messages for this channel so far
        # they could be added in the future
        return False

    def post_message(self, message):
        logger.info(
            "Sending message %s to the %s",
            message,
            self.CONFIG["ChannelUrl"]
        )

        relative_url = (
            # for debug and dumb channels
            "/messages"
            if "httpbin" not in self.CONFIG['ChannelUrl']
            else "/post"
        )

        payload = message.to_dict()
        del payload["sender_ref"]
        del payload["status"]

        resp = requests.post(
            f"{self.CONFIG['ChannelUrl']}{relative_url}",
            json=payload,
            headers=self._get_headers(),
        )
        if str(resp.status_code).startswith("2"):
            # this ID has any meaning only for channel and notifications from it
            ch_msg_id = resp.json().get("id") or None
            result = ch_msg_id
            logger.info(
                "Have sent %s with resp %s, message ID is %s",
                message.sender_ref, resp.json(), ch_msg_id
            )
            self._subscribe_to_message(ch_msg_id)
            # TODO: return message reference or so to subscribe to updates
        else:
            result = False
            logger.error(
                "Error sending %s: %s", message.sender_ref, resp.content
            )
        return result

    def get_messages(self):
        raise NotImplementedError()

    def _get_headers(self):
        result = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.CONFIG["ChannelAuth"] == "Cognito/JWT":
            auth_header = "Bearer " + self._get_cached_cognito_jwt()
            result["Authorization"] = auth_header
        return result

    def _get_cached_cognito_jwt(self):
        """
        This is implementation-specific procedure. Good thing - it's useful
        and will be used for our test installations.
        Bad thing - it's really cognito-specific. In fact it could be easily
        changed to generic OIDC IDP.
        Good thing - it could be moved to a subclass easily, preserving the core
        intergov pureness
        """
        old_token_exp = getattr(self, "_cognito_jwt_expiration_date", None)
        old_token_value = getattr(self, "_cognito_jwt", None)

        if old_token_exp and old_token_exp < datetime.datetime.utcnow():
            old_token_value = None

        if old_token_value:
            # cache hit
            return old_token_value

        new_token, expires = self._issue_cognito_jwt()
        self._cognito_jwt = new_token
        if expires < 60:
            seconds_to_renew = int(expires / 2)
        else:
            seconds_to_renew = expires - 60
        self._cognito_jwt_expiration_date = (
            datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds_to_renew)
        )
        return new_token

    def _issue_cognito_jwt(self):
        # see _get_cached_cognito_jwt descr about the design concerns
        OAUTH_CLIENT_ID = env("IGL_OAUTH_CLIENT_ID", default=None)
        OAUTH_CLIENT_SECRET = env("IGL_OAUTH_CLIENT_SECRET", default=None)
        OAUTH_SCOPES = env("IGL_OAUTH_SCOPES", default=None)

        cognito_auth = base64.b64encode(
            f"{OAUTH_CLIENT_ID}:{OAUTH_CLIENT_SECRET}".encode("utf-8")
        ).decode("utf-8")
        token_resp = requests.post(
            _oidc_token_url(),
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
        logger.info("Retrieved new JWT; ends in %s", json_resp['expires_in'])
        return json_resp["access_token"], json_resp['expires_in']

    def _subscribe_to_message(self, ch_msg_id):
        logger.warning(
            "Although we have to subscribe to channel %s message %s updates,"
            " it's not implemented yet",
            self, ch_msg_id,
        )


@lru_cache(maxsize=2)  # it's fine to cache for a long time
def _oidc_token_url():
    # see _get_cached_cognito_jwt descr about the design concerns
    token_endpoint = env("IGL_OAUTH_TOKEN_ENDPOINT", default=None) or ""
    if token_endpoint:
        # we have token endpoint provided directly to save us requests
        return token_endpoint
    wnurl = env("IGL_OAUTH_WELLKNOWN_URL")
    if not wnurl:
        raise Exception(
            "HttpApiChannel uses Cognit/JWT auth but you haven't configured "
            "env variables correctly, and they are required to issue the token"
        )
    wellknown_content = requests.get(wnurl)
    assert wellknown_content.status_code == 200
    return wellknown_content.json().get("token_endpoint")

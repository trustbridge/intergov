from libtrustbridge.utils.conf import env, env_json

MESSAGE_PATCH_API_ENDPOINT = env(
    'IGL_PROC_BCH_MESSAGE_API_ENDPOINT',
    default='http://message_api/message/{sender}:{sender_ref}'
)
MESSAGE_PATCH_API_ENDPOINT_AUTH = env(
    "IGL_PROC_BCH_MESSAGE_API_ENDPOINT_AUTH",
    default="Cognito/JWT"
)
MESSAGE_PATCH_API_ENDPOINT_AUTH_PARAMS = None

if MESSAGE_PATCH_API_ENDPOINT_AUTH == "Cognito/JWT":
    # These env variables may change in the future
    JRD = env("IGL_COUNTRY")
    MESSAGE_PATCH_API_ENDPOINT_AUTH_PARAMS = {
        "client_id": env_json("IGL_COUNTRY_OAUTH_CLIENT_ID")[JRD],
        "client_secret": env_json("IGL_COUNTRY_OAUTH_CLIENT_SECRET")[JRD],
        "scopes": env_json("IGL_COUNTRY_OAUTH_SCOPES")[JRD],
        "wellknown_url": env_json("IGL_COUNTRY_OAUTH_WELLKNOWN_URL")[JRD],
    }



MESSAGE_RX_API_URL = env(
    'IGL_PROC_BCH_MESSAGE_RX_API_URL',
    default='http://message_rx_api'
)

COUNTRY = env("IGL_COUNTRY", 'AU')


# url to channel endpoint for subscription by jurisdiction
# i.e https://shared-db-channel-api:8001/messages/subscriptions/by_jurisdiction
CHANNEL_SUBSCRIBE_URL = env("IGL_PROC_SUBSCRIBE_URL")

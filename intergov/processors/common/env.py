from libtrustbridge.utils.conf import env, env_json

MESSAGE_PATCH_API_ENDPOINT = env(
    'IGL_PROC_BCH_MESSAGE_API_ENDPOINT',
    default='http://message_api/message/{sender}:{sender_ref}'
)

COGNITO_JWT_AUTH = "Cognito/JWT"
MESSAGE_PATCH_API_ENDPOINT_AUTH = env(
    "IGL_PROC_BCH_MESSAGE_API_ENDPOINT_AUTH",
    default=COGNITO_JWT_AUTH
)

MESSAGE_RX_API_URL = env(
    'IGL_PROC_BCH_MESSAGE_RX_API_URL',
    default='http://message_rx_api'
)

COUNTRY = env("IGL_COUNTRY", 'AU')

ROUTING_TABLE = env_json("IGL_MCHR_ROUTING_TABLE")

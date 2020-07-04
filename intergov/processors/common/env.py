import hashlib

from libtrustbridge.utils.conf import env, env_json

from intergov.loggers import logging

logger = logging.getLogger(__name__)


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

ROUTING_TABLE = env_json("IGL_MCHR_ROUTING_TABLE", default=[])

for i, rule in enumerate(ROUTING_TABLE):
    if "Id" not in rule:
        logger.warning("Wrong channel configuration: no ID for line %s", i)
        rule["Id"] = hashlib.md5("lala".encode("utf-8")).hexdigest() + str(i)

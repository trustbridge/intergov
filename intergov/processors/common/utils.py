from libtrustbridge.utils.conf import env, env_json

from intergov.processors.common.env import MESSAGE_PATCH_API_ENDPOINT_AUTH, COGNITO_JWT_AUTH


def get_message_patch_api_endpoint_auth_params():
    if MESSAGE_PATCH_API_ENDPOINT_AUTH == COGNITO_JWT_AUTH:
        # These env variables may change in the future
        jurisdiction = env("IGL_JURISDICTION")
        return {
            "client_id": env_json("IGL_JURISDICTION_OAUTH_CLIENT_ID")[jurisdiction],
            "client_secret": env_json("IGL_JURISDICTION_OAUTH_CLIENT_SECRET")[jurisdiction],
            "scopes": env_json("IGL_JURISDICTION_OAUTH_SCOPES")[jurisdiction],
            "wellknown_url": env_json("IGL_JURISDICTION_OAUTH_WELLKNOWN_URL")[jurisdiction],
        }


def get_channels_to_subscribe_as(routing_table, jurisdiction):
    # just skip the self channel configuration
    return [c for c in routing_table if c['Jurisdiction'] != jurisdiction]

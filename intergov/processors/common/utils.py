from libtrustbridge.utils.conf import env, env_json

from intergov.processors.common.env import MESSAGE_PATCH_API_ENDPOINT_AUTH, COGNITO_JWT_AUTH


def get_message_patch_api_endpoint_auth_params():
    if MESSAGE_PATCH_API_ENDPOINT_AUTH == COGNITO_JWT_AUTH:
        # These env variables may change in the future
        JRD = env("IGL_COUNTRY")
        return {
            "client_id": env_json("IGL_COUNTRY_OAUTH_CLIENT_ID")[JRD],
            "client_secret": env_json("IGL_COUNTRY_OAUTH_CLIENT_SECRET")[JRD],
            "scopes": env_json("IGL_COUNTRY_OAUTH_SCOPES")[JRD],
            "wellknown_url": env_json("IGL_COUNTRY_OAUTH_WELLKNOWN_URL")[JRD],
        }


def get_channels_for_local_jurisdiction(routing_table, country):
    return [c for c in routing_table if c['Jurisdiction'] == country]

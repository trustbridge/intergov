from intergov.conf import env, env_s3_config, env_bool, env_queue_config


class Config(object):
    """Base configuration."""
    DEBUG = env_bool('IGL_DEBUG', default=True)
    TESTING = env_bool('IGL_TESTING', default=True)

    MESSAGE_LAKE_CONN = env_s3_config('MSGAPI_MESSAGE_LAKE')

    BC_INBOX_CONF = env_queue_config('MSG_RX_API_BC_INBOX')

    PUBLISH_NOTIFICATIONS_REPO_CONN = env_queue_config('MSG_RX_API_OUTBOX_REPO')

    SENTRY_DSN = env("SENTRY_DSN", default=None)


class TestConfig(Config):
    # Use separate conf object only for tests
    DEBUG = True
    TESTING = True
    SENTRY_DSN = None

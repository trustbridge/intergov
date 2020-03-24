from intergov.conf import env_bool, env_queue_config


class Config(object):
    """Base configuration."""
    DEBUG = env_bool('IGL_DEBUG', default=True)
    TESTING = env_bool('IGL_TESTING', default=True)

    BC_INBOX_CONF = env_queue_config('MSG_RX_API_BC_INBOX')


class TestConfig(Config):
    # Use separate conf object only for tests - to conditionless disable emails, etc
    DEBUG = True
    TESTING = True

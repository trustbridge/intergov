from libtrustbridge.utils.conf import env_bool, env_json, env_queue_config


class Config(object):
    """Base configuration."""
    DEBUG = env_bool('IGL_DEBUG', default=True)
    TESTING = env_bool('IGL_TESTING', default=True)

    CHANNEL_NOTIFICATION_REPO_CONF = env_queue_config('CHANNEL_NOTIFICATION_REPO')
    ROUTING_TABLE = env_json("IGL_MCHR_ROUTING_TABLE")


class TestConfig(Config):
    # Use separate conf object only for tests - to conditionless disable emails, etc
    DEBUG = True
    TESTING = True

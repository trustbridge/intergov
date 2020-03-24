from intergov.conf import env_s3_config, env_bool


class Config(object):
    """Base configuration."""
    DEBUG = env_bool('IGL_DEBUG', default=True)
    TESTING = env_bool('IGL_TESTING', default=True)
    SUBSCR_REPO_CONF = env_s3_config('SUBSCR_API_REPO')


class TestConfig(Config):
    # Use separate conf object only for tests
    DEBUG = True
    TESTING = True

from intergov.conf import env, env_bool, env_s3_config


class Config(object):
    """Base configuration."""
    DEBUG = env_bool('IGL_DEBUG', default=True)
    TESTING = env_bool('IGL_TESTING', default=True)
    OBJECT_LAKE_CONN = env_s3_config('DOCAPI_OBJ_LAKE')
    OBJECT_ACL_CONN = env_s3_config('DOCAPI_OBJ_ACL')


class TestConfig(Config):
    # Use separate conf object only for tests
    DEBUG = True
    TESTING = True

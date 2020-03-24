import os
import json
from unittest import mock
import pytest
from intergov import conf


TEST_ENV_NONE_KEY = "TEST_ENV_NONE_KEY"
TEST_ENV_JSON_KEY = "TEST_ENV_JSON_KEY"
TEST_ENV_BOOL_VALUE_KEY = "TEST_ENV_BOOL_VALUE_KEY"

TEST_DEFAULT = "TEST_DEFAULT_VALUE"
TEST_NON_DEFAULT_VALUE = "TEST_NON_DEFAUT_VALUE"

TEST_ENV_JSON_DICT = {
    "one": "one_value",
    "two": "two_value"
}

TEST_ENV_JSON_DEFAULT = [
    "1",
    "2",
    "3"
]

TEST_ENV_INVALID_JSON_STR = "{heelo:world}"

TEST_ENV_BOOL_VALUES = [
    ('true', True),
    ('false', False),
    ('TruE', True),
    ('fAlse', False),
]


def test_simple():
    # test env_none
    assert not os.environ.get(TEST_ENV_NONE_KEY)
    assert not conf.env_none(TEST_ENV_NONE_KEY)
    assert TEST_DEFAULT == conf.env_none(TEST_ENV_NONE_KEY, default=TEST_DEFAULT)
    os.environ[TEST_ENV_NONE_KEY] = TEST_NON_DEFAULT_VALUE
    assert TEST_NON_DEFAULT_VALUE == conf.env_none(TEST_ENV_NONE_KEY, default=TEST_DEFAULT)
    os.environ[TEST_ENV_NONE_KEY] = ""
    assert conf.env_none(TEST_ENV_NONE_KEY) is None

    # test env_bool
    assert not os.environ.get(TEST_ENV_BOOL_VALUE_KEY)
    for env_value, value in TEST_ENV_BOOL_VALUES:
        os.environ[TEST_ENV_BOOL_VALUE_KEY] = env_value
        assert conf.env_bool(TEST_ENV_BOOL_VALUE_KEY) == value

    del os.environ[TEST_ENV_BOOL_VALUE_KEY]
    assert conf.env_bool(TEST_ENV_BOOL_VALUE_KEY, default=True)
    assert conf.env_bool(TEST_ENV_BOOL_VALUE_KEY, default=None, nullable=True) is None

    os.environ[TEST_ENV_BOOL_VALUE_KEY] = 'False'
    assert conf.env_bool(TEST_ENV_BOOL_VALUE_KEY, default=True) is False

    # not none exception
    del os.environ[TEST_ENV_BOOL_VALUE_KEY]
    with pytest.raises(Exception) as e:
        conf.env_bool(TEST_ENV_BOOL_VALUE_KEY, nullable=False, default=None)

    assert str(e.value) == "Variable {} can't be None".format(
        TEST_ENV_BOOL_VALUE_KEY
    )
    # unknown string value
    os.environ[TEST_ENV_BOOL_VALUE_KEY] = "FalseFalseTrue"
    with pytest.raises(Exception) as e:
        conf.env_bool(TEST_ENV_BOOL_VALUE_KEY)

    assert str(e.value) == "Unknown value for variable {}: '{}'".format(
        TEST_ENV_BOOL_VALUE_KEY,
        os.environ[TEST_ENV_BOOL_VALUE_KEY]
    )

    # invalid default value
    del os.environ[TEST_ENV_BOOL_VALUE_KEY]
    with pytest.raises(Exception) as e:
        conf.env_bool(TEST_ENV_BOOL_VALUE_KEY, default=dict(msg="Hello"))

    assert str(e.value) == "Unknown value type for variable {}: '{}'".format(
        TEST_ENV_BOOL_VALUE_KEY,
        dict
    )

    # test env_json
    assert not os.environ.get(TEST_ENV_JSON_KEY)
    os.environ[TEST_ENV_JSON_KEY] = json.dumps(TEST_ENV_JSON_DICT)
    assert conf.env_json(TEST_ENV_JSON_KEY) == TEST_ENV_JSON_DICT
    del os.environ[TEST_ENV_JSON_KEY]
    assert conf.env_json(TEST_ENV_JSON_KEY, default=TEST_ENV_JSON_DEFAULT) == TEST_ENV_JSON_DEFAULT

    os.environ[TEST_ENV_JSON_KEY] = TEST_ENV_INVALID_JSON_STR
    with pytest.raises(ValueError):
        conf.env_json(TEST_ENV_JSON_KEY)


TEST_S3_DEFAULT_CONF = {
    'use_ssl': 'False',
    'host': 'b',
    'port': 'c',
    'bucket': 'd',
    'region': 'e',
    'secret_key': 'f',
    'access_key': 'j'
}


def igl_value(prefix, value):
    return f'IGL_{prefix.upper()}_{value.upper()}'


TEST_ENV_S3_DEFAULT = {
    igl_value('default_s3', 'use_ssl'): TEST_S3_DEFAULT_CONF['use_ssl'],
    igl_value('default_s3', 'host'): TEST_S3_DEFAULT_CONF['host'],
    igl_value('default_s3', 'port'): TEST_S3_DEFAULT_CONF['port'],
    igl_value('default_s3', 'bucket'): TEST_S3_DEFAULT_CONF['bucket'],
    igl_value('default_s3', 'region'): TEST_S3_DEFAULT_CONF['region'],
    igl_value('default_s3', 'secret_key'): TEST_S3_DEFAULT_CONF['secret_key'],
    igl_value('default_s3', 'access_key'): TEST_S3_DEFAULT_CONF['access_key']
}


TEST_SQS_DEFAULT_CONF = {
    'use_ssl': 'False',
    'host': '2',
    'port': '3',
    'queue_name': '4',
    'region': '5',
    'secret_key': '6',
    'access_key': '7'
}

TEST_ENV_SQS_DEFAULT = {
    igl_value('default_sqs', 'use_ssl'): TEST_SQS_DEFAULT_CONF['use_ssl'],
    igl_value('default_sqs', 'host'): TEST_SQS_DEFAULT_CONF['host'],
    igl_value('default_sqs', 'port'): TEST_SQS_DEFAULT_CONF['port'],
    igl_value('default_sqs', 'qname'): TEST_SQS_DEFAULT_CONF['queue_name'],
    igl_value('default_sqs', 'region'): TEST_SQS_DEFAULT_CONF['region'],
    igl_value('default_sqs', 'secret_key'): TEST_SQS_DEFAULT_CONF['secret_key'],
    igl_value('default_sqs', 'access_key'): TEST_SQS_DEFAULT_CONF['access_key']
}

TEST_POSTGRES_DEFAULT_CONF = {
    'host': '1a',
    'user': '2b',
    'password': '3c',
    'dbname': '4d'
}

TEST_ENV_POSTGRES_DEFAULT = {
    igl_value('default_postgres', 'host'): TEST_POSTGRES_DEFAULT_CONF['host'],
    igl_value('default_postgres', 'user'): TEST_POSTGRES_DEFAULT_CONF['user'],
    igl_value('default_postgres', 'password'): TEST_POSTGRES_DEFAULT_CONF['password'],
    igl_value('default_postgres', 'dbname'): TEST_POSTGRES_DEFAULT_CONF['dbname']
}


CUSTOM_S3_CONF = {}
for key, value in TEST_S3_DEFAULT_CONF.items():
    CUSTOM_S3_CONF[key] = value*2
CUSTOM_S3_CONF['use_ssl'] = True

CUSTOM_SQS_CONF = {}
for key, value in TEST_SQS_DEFAULT_CONF.items():
    CUSTOM_SQS_CONF[key] = f"{key}:{value}"*2
CUSTOM_SQS_CONF['use_ssl'] = True

CUSTOM_POSTGRES_CONF = {}
for key, value in TEST_POSTGRES_DEFAULT_CONF.items():
    CUSTOM_POSTGRES_CONF[key] = f"{key}:{key}:{value}".upper()

CUSTOM_S3_CONF_NAME = "CUSTOM_S3_CONF_NAME"
CUSTOM_SQS_CONF_NAME = "CUSTOM_SQS_CONF_NAME"
CUSTOM_POSTGRES_CONF_NAME = "CUSTOM_POSTGRES_CONF_NAME"

TEST_ENV_CUSTOM_S3_CONF = {
    igl_value(CUSTOM_S3_CONF_NAME, 'use_ssl'): str(CUSTOM_S3_CONF['use_ssl']),
    igl_value(CUSTOM_S3_CONF_NAME, 'host'): CUSTOM_S3_CONF['host'],
    igl_value(CUSTOM_S3_CONF_NAME, 'port'): CUSTOM_S3_CONF['port'],
    igl_value(CUSTOM_S3_CONF_NAME, 'bucket'): CUSTOM_S3_CONF['bucket'],
    igl_value(CUSTOM_S3_CONF_NAME, 'region'): CUSTOM_S3_CONF['region'],
    igl_value(CUSTOM_S3_CONF_NAME, 'secret_key'): CUSTOM_S3_CONF['secret_key'],
    igl_value(CUSTOM_S3_CONF_NAME, 'access_key'): CUSTOM_S3_CONF['access_key']
}
TEST_ENV_CUSTOM_SQS_CONF = {
    igl_value(CUSTOM_SQS_CONF_NAME, 'use_ssl'): str(CUSTOM_SQS_CONF['use_ssl']),
    igl_value(CUSTOM_SQS_CONF_NAME, 'host'): CUSTOM_SQS_CONF['host'],
    igl_value(CUSTOM_SQS_CONF_NAME, 'port'): CUSTOM_SQS_CONF['port'],
    igl_value(CUSTOM_SQS_CONF_NAME, 'qname'): CUSTOM_SQS_CONF['queue_name'],
    igl_value(CUSTOM_SQS_CONF_NAME, 'region'): CUSTOM_SQS_CONF['region'],
    igl_value(CUSTOM_SQS_CONF_NAME, 'secret_key'): CUSTOM_SQS_CONF['secret_key'],
    igl_value(CUSTOM_SQS_CONF_NAME, 'access_key'): CUSTOM_SQS_CONF['access_key']
}

TEST_ENV_CUSTOM_POSTGRES_CONF = {
    igl_value(CUSTOM_POSTGRES_CONF_NAME, 'host'): CUSTOM_POSTGRES_CONF['host'],
    igl_value(CUSTOM_POSTGRES_CONF_NAME, 'user'): CUSTOM_POSTGRES_CONF['user'],
    igl_value(CUSTOM_POSTGRES_CONF_NAME, 'password'): CUSTOM_POSTGRES_CONF['password'],
    igl_value(CUSTOM_POSTGRES_CONF_NAME, 'dbname'): CUSTOM_POSTGRES_CONF['dbname']
}

TEST_ENV = {
    **TEST_ENV_S3_DEFAULT,
    **TEST_ENV_SQS_DEFAULT,
    **TEST_ENV_POSTGRES_DEFAULT,
    **TEST_ENV_CUSTOM_S3_CONF,
    **TEST_ENV_CUSTOM_POSTGRES_CONF,
    **TEST_ENV_CUSTOM_SQS_CONF
}


TEST_NON_EXISTING_CONF_NAME = "TEST_NON_EXISTING_CONF_NAME"


def to_str_dict(data):
    result = {}
    for key, value in data.items():
        result[key] = str(value)
    return result


@mock.patch.dict(os.environ, TEST_ENV)
def test_complex():

    assert igl_value('default_sqs', 'qname') == 'IGL_DEFAULT_SQS_QNAME'
    assert igl_value('default_s3', 'bucket') == 'IGL_DEFAULT_S3_BUCKET'
    assert igl_value('default_postgres', 'dbname') == 'IGL_DEFAULT_POSTGRES_DBNAME'

    for key, value in TEST_ENV.items():
        assert os.environ.get(key) == value

    default_s3_conf = conf.env_s3_config(TEST_NON_EXISTING_CONF_NAME)
    default_sqs_conf = conf.env_queue_config(TEST_NON_EXISTING_CONF_NAME)
    default_postgres_conf = conf.env_postgres_config(TEST_NON_EXISTING_CONF_NAME)

    assert to_str_dict(default_s3_conf) == TEST_S3_DEFAULT_CONF
    assert to_str_dict(default_sqs_conf) == TEST_SQS_DEFAULT_CONF
    assert to_str_dict(default_postgres_conf) == TEST_POSTGRES_DEFAULT_CONF

    # bool values
    assert isinstance(default_s3_conf['use_ssl'], bool)
    assert isinstance(default_sqs_conf['use_ssl'], bool)

    # nullable values
    del os.environ['IGL_DEFAULT_SQS_QNAME']
    del os.environ['IGL_DEFAULT_S3_BUCKET']
    del os.environ['IGL_DEFAULT_POSTGRES_DBNAME']

    default_s3_conf = conf.env_s3_config(TEST_NON_EXISTING_CONF_NAME)
    default_sqs_conf = conf.env_queue_config(TEST_NON_EXISTING_CONF_NAME)
    default_postgres_conf = conf.env_postgres_config(TEST_NON_EXISTING_CONF_NAME)

    assert default_s3_conf['bucket'] is None
    assert default_sqs_conf['queue_name'] is None
    assert default_postgres_conf['dbname'] is None

    # testing fully custom configs
    custom_s3_conf = conf.env_s3_config(CUSTOM_S3_CONF_NAME)
    custom_sqs_conf = conf.env_queue_config(CUSTOM_SQS_CONF_NAME)
    custom_postgres_conf = conf.env_postgres_config(CUSTOM_POSTGRES_CONF_NAME)

    assert custom_s3_conf == CUSTOM_S3_CONF, os.environ
    assert custom_sqs_conf == CUSTOM_SQS_CONF, os.environ
    assert custom_postgres_conf == CUSTOM_POSTGRES_CONF, os.environ

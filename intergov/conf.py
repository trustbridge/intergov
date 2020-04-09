"""
We need a way of picking up config from the environment
and passing it to services (apis, containers, etc)

This file contains base utils and may be some global config to be importer
as `from integrov.conf import ...`

Specific modules should have their own conf.py file, to not mix such different
things used only from the module itself in the global namespace.
"""
import base64
import json
import logging
import os

BASE64_PREFIX_1 = 'base64:'
BASE64_PREFIX_2 = 'kms+base64:'
AWS_REGION = os.environ.get('AWS_REGION', None)


# Existing libraries do it better, but for the simplest case we may be fine with
# such simple code written, to avoid extra dependencies and build delays
def env(name, default=None):
    if name in os.environ:
        value = string_or_b64kms(os.environ[name])
    else:
        value = default
    return value


# Allows for an empty string to be treated as None rather than empty string
def env_none(name, default=None):
    if name in os.environ:
        val = string_or_b64kms(os.environ[name])
    else:
        val = default
    if isinstance(val, str):
        if not val:
            return None
        else:
            return val
    else:
        return val


def env_bool(name, default=None, nullable=False):
    if name in os.environ:
        val = string_or_b64kms(os.environ[name])
    else:
        val = default
    if val is None:
        if not nullable:
            raise Exception("Variable {} can't be None".format(name))
        return val
    if isinstance(val, str):
        val_lower = val.strip().lower()
        if val_lower == 'true':
            return True
        if val_lower == 'false':
            return False
        raise Exception("Unknown value for variable {}: '{}'".format(name, val))
    elif isinstance(val, bool):
        return val
    else:
        raise Exception("Unknown value type for variable {}: '{}'".format(name, type(val)))


def env_json(name, default=None):
    if name in os.environ:
        val = string_or_b64kms(os.environ[name])
        val = json.loads(val)
    else:
        val = default
    return val


def decrypt_kms_data(encrypted_data):
    """Decrypt KMS encoded data."""
    import boto3  # local import so we don't need it installed for demo and local
    if not AWS_REGION:
        logging.error(
            "Trying to decrypt KMS value but no AWS region set"
        )
        return None

    kms = boto3.client('kms', region_name=AWS_REGION)
    decrypted = kms.decrypt(CiphertextBlob=encrypted_data)

    if decrypted.get('KeyId'):
        # Decryption succeed
        decrypted_value = decrypted.get('Plaintext', '')
        if isinstance(decrypted_value, bytes):
            decrypted_value = decrypted_value.decode('utf-8')
        return decrypted_value


def string_or_b64kms(value):
    """Check if value is base64 encoded - if yes, decode it using KMS."""

    if not value:
        return value

    try:
        # Check if environment value base64 encoded
        if isinstance(value, (str, bytes)):
            encrypted_value = None
            if value.startswith(BASE64_PREFIX_1):
                encrypted_value = value[len(BASE64_PREFIX_1):]
            elif value.startswith(BASE64_PREFIX_2):
                encrypted_value = value[len(BASE64_PREFIX_2):]
            else:
                # non-encrypted value
                return value
            # If yes, decode it using AWS KMS
            data = base64.b64decode(encrypted_value)
            decrypted_value = decrypt_kms_data(data)

            # If decryption succeed, use it
            if decrypted_value:
                value = decrypted_value
    except Exception as e:
        logging.exception(e)
    return value


def env_s3_config(prefix):
    """
    Usage:
    OBJECT_LAKE_CONN = env_s3_config('DOCAPI_OBJ_LAKE')

    Full-default configuration is made for docker-compose.yml minio instance
    But can be easily replaced to external S3 or minio either globally
    (for all S3 repos, in this case leave specific variables undefined):

        IGL_DEFAULT_S3_USE_SSL=True
        IGL_DEFAULT_S3_REGION=eu-central-1
        IGL_DEFAULT_S3_HOST=minio.int
        IGL_DEFAULT_S3_PORT=9000
        IGL_DEFAULT_S3_ACCESS_KEY=minidemoaccess
        IGL_DEFAULT_S3_SECRET_KEY=miniodemosecret

        or

        IGL_DEFAULT_S3_USE_SSL=True
        IGL_DEFAULT_S3_REGION=eu-central-1
        IGL_DEFAULT_S3_HOST=s3-eu-central-1.amazonaws.com
        IGL_DEFAULT_S3_PORT=443
        IGL_DEFAULT_S3_BUCKET=icl-universal-storage
        IGL_DEFAULT_S3_ACCESS_KEY=AKIA....
        IGL_DEFAULT_S3_SECRET_KEY=wwVQnp0....

    Or locally, only for this one:

        IGL_DOCAPI_OBJ_LAKE_USE_SSL=...
        IGL_DOCAPI_OBJ_LAKE_HOST=...
        ...

    Specific service variables win. The best place to put this code is `demo-dc.env` file.

    """
    config = {
        'use_ssl': env_bool(
            f'IGL_{prefix}_USE_SSL',
            default=env('IGL_DEFAULT_S3_USE_SSL')
        ),
        'host': env(
            f'IGL_{prefix}_HOST',
            default=env('IGL_DEFAULT_S3_HOST')
        ),
        'port': env(
            f'IGL_{prefix}_PORT',
            default=env('IGL_DEFAULT_S3_PORT')
        ),
        'bucket': env(
            # None means "repo handles the default bucket name"
            f'IGL_{prefix}_BUCKET',
            default=env('IGL_DEFAULT_S3_BUCKET', default=None)
        ),
        'region': env(
            f'IGL_{prefix}_REGION',
            default=env('IGL_DEFAULT_S3_REGION')
        ),
        'secret_key': env(
            f'IGL_{prefix}_SECRET_KEY',
            default=env('IGL_DEFAULT_S3_SECRET_KEY')
        ) or None,
        'access_key': env(
            f'IGL_{prefix}_ACCESS_KEY',
            default=env('IGL_DEFAULT_S3_ACCESS_KEY')
        ) or None,
    }
    return config


def env_queue_config(prefix):
    """
    Usage:
    BC_INBOX_CONF = env_queue_config('MSG_RX_API_BC_INBOX')

    Full-default configuration is made for docker-compose.yml elasticmq instance
    But can be easily replaced to external SQS either globally
    """
    config = {
        'use_ssl': env_bool(
            f'IGL_{prefix}_USE_SSL',
            default=env('IGL_DEFAULT_SQS_USE_SSL')
        ),
        'host': env(
            f'IGL_{prefix}_HOST',
            default=env('IGL_DEFAULT_SQS_HOST')
        ),
        'port': env(
            f'IGL_{prefix}_PORT',
            default=env('IGL_DEFAULT_SQS_PORT')
        ),
        'queue_name': env(
            # None means "repo handles the default queue name"
            f'IGL_{prefix}_QNAME',
            default=env('IGL_DEFAULT_SQS_QNAME', default=None)
        ),
        'region': env(
            f'IGL_{prefix}_REGION',
            default=env('IGL_DEFAULT_SQS_REGION')
        ),
        'secret_key': env(
            f'IGL_{prefix}_SECRET_KEY',
            default=env('IGL_DEFAULT_SQS_SECRET_KEY')
        ) or None,
        'access_key': env(
            f'IGL_{prefix}_ACCESS_KEY',
            default=env('IGL_DEFAULT_SQS_ACCESS_KEY')
        ) or None,
    }
    return config


def env_postgres_config(prefix):
    config = {
        'host': env(
            f'IGL_{prefix}_HOST',
            default=env('IGL_DEFAULT_POSTGRES_HOST')
        ),
        'user': env(
            f'IGL_{prefix}_USER',
            default=env('IGL_DEFAULT_POSTGRES_USER')
        ),
        'password': env(
            f'IGL_{prefix}_PASSWORD',
            default=env('IGL_DEFAULT_POSTGRES_PASSWORD')
        ),
        'dbname': env(
            f'IGL_{prefix}_DBNAME',
            default=env('IGL_DEFAULT_POSTGRES_DBNAME', default=None)
        )
    }

    return config


# Statd monitoring (if enabled)
# We have these configuration values global for all our sub-components
# because it's simpler
STATSD_HOST = env_none('MON_STATSD_HOST', default=None)
if STATSD_HOST:
    STATSD_PREFIX = env_none('MON_STATSD_PREFIX', default='intergov')
    STATSD_PORT = int(env_none('MON_STATSD_PORT', default=8125))

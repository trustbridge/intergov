import os
import logging
from logging.config import dictConfig

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

from intergov.conf import env_bool, env

SENTRY_DSN = env('SENTRY_DSN', default=None)

if SENTRY_DSN:  # pragma: no cover
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[LoggingIntegration(), AwsLambdaIntegration()]
    )

    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("service", "intergov")
        scope.set_tag("country", env("ICL_APP_COUNTRY", default=""))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)-15s %(levelname)s [%(name)s] %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'botocore': {
            'level': 'INFO'
        },
        'urllib3': {
            'level': 'INFO'
        },
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }

}

# JSON formatter for sending logs to ES
LOG_FORMATTER_JSON = env_bool('ICL_LOG_FORMATTER_JSON', default=False)
if LOG_FORMATTER_JSON:  # pragma: no cover
    LOGGING['formatters']['json'] = {
        '()': 'intergov.json_log_formatter.JsonFormatter',
    }
    LOGGING['handlers']['console']['formatter'] = 'json'

# Apply the config
dictConfig(LOGGING)
logger = logging.getLogger('intergov')

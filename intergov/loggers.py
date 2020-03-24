import logging
from logging.config import dictConfig
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from intergov.conf import env_bool, env


SENTRY_DSN = env('SENTRY_DSN', default=None)

if SENTRY_DSN:  # pragma: no cover
    sentry_logging = LoggingIntegration(
        level=logging.INFO,        # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[sentry_logging]
    )


LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s[%(name)s] %(message)s'
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
        'level': 'INFO',
    },
    '': {
        'handlers': ['console'],
        'level': 'INFO',
    },
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

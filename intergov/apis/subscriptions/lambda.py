import logging

from intergov.apis.subscriptions.conf import Config
from intergov.apis.subscriptions.app import create_app

logger = logging.getLogger(__name__)

logger.info('Starting subscriptions app')

app = create_app(Config())

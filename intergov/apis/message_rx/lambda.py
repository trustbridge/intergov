import logging

from intergov.apis.message_rx.conf import Config
from intergov.apis.message_rx.app import create_app

logger = logging.getLogger(__name__)

logger.info('Starting message_rx app')

app = create_app(Config())

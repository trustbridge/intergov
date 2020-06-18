from intergov.apis.message_rx.conf import Config
from intergov.apis.message_rx.app import create_app
from intergov.loggers import logging

logger = logging.getLogger(__name__)

logger.info('Starting message_rx app')

app = create_app(Config())

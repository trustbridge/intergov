from intergov.apis.message.conf import Config
from intergov.apis.message.app import create_app
from intergov.loggers import logging

logger = logging.getLogger(__name__)

logger.info('Starting message app')

app = create_app(Config())

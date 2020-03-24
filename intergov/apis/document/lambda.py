import logging

from intergov.apis.document.conf import Config
from intergov.apis.document.app import create_app

logger = logging.getLogger(__name__)

logger.info('Starting document app')

app = create_app(Config())

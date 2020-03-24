from flask import Flask, Response

from intergov.apis.common.errors import handlers
from intergov.loggers import logging  # NOQA

logger = logging.getLogger('dummy-test-helper')

app = Flask(__name__)
handlers.register(app)


@app.route('/response/<int:status_code>/<message>', methods=['GET', 'POST'])
def request_response(status_code, message):
    logger.info(f'Requested response with status: {status_code} and message:{message}')
    return Response(
        message,
        status=status_code
    )

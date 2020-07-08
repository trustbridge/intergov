from flask import Flask

from intergov.apis.common.errors import handlers
from intergov.apis.message import message, index
from intergov.apis.message.conf import Config
from intergov.loggers import logging  # NOQA


def create_app(config_object=None):
    """
    FLASK_ENV=development FLASK_APP=message_api.app flask run --port=5001
    """
    if config_object is None:
        config_object = Config
    app = Flask(__name__)
    app.config.from_object(config_object)
    SENTRY_DSN = app.config.get("SENTRY_DSN")
    if SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
        sentry_sdk.init(SENTRY_DSN, integrations=[FlaskIntegration(), AwsLambdaIntegration()])
    app.register_blueprint(index.blueprint)
    app.register_blueprint(message.blueprint)
    handlers.register(app)
    return app

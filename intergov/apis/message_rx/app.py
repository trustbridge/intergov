from flask import Flask

from intergov.apis.common.errors import handlers
from intergov.apis.message_rx import message, index
from intergov.apis.message_rx.conf import Config
from intergov.loggers import logging  # NOQA


def create_app(config_object=None):
    """
    PYTHONPATH=".;../" FLASK_ENV=development FLASK_APP=app flask run
    """
    if config_object is None:
        config_object = Config
    app = Flask(__name__)
    app.config.from_object(config_object)
    SENTRY_DSN = app.config.get("SENTRY_DSN")
    if SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(SENTRY_DSN, integrations=[FlaskIntegration()])
    app.register_blueprint(index.blueprint)
    app.register_blueprint(message.blueprint)
    handlers.register(app)
    return app

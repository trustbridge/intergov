from flask import Flask

from intergov.apis.subscriptions import subscriptions, index
from intergov.apis.subscriptions.conf import Config
from libtrustbridge.errors import handlers


def create_app(config_object=None):
    """
    FLASK_ENV=development FLASK_APP=apis.subscriptions.app flask run
    """
    if config_object is None:
        config_object = Config
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.register_blueprint(index.blueprint)
    app.register_blueprint(subscriptions.blueprint)
    handlers.register(app)
    return app

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask import Flask
from libtrustbridge.utils.specs import register_specs

from intergov.apis.subscriptions import subscriptions, index
from intergov.apis.subscriptions.conf import Config
from libtrustbridge.errors import handlers


spec = APISpec(
        title="Subscription API",
        version="1.0.0",
        openapi_version="3.0.2",
        plugins=[
            FlaskPlugin(),
            MarshmallowPlugin(),
        ],
    )


def create_app(config_object=None):
    """
    FLASK_ENV=development FLASK_APP=apis.subscriptions.app flask run
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
    app.register_blueprint(subscriptions.blueprint)
    handlers.register(app)
    register_specs(app, spec, ('subscription_register', ))
    return app

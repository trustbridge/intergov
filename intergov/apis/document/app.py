from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask import Flask
from flask.wrappers import Request
from libtrustbridge.utils.specs import register_specs

from intergov.apis.common.errors import handlers
from intergov.apis.document import documents, index
from intergov.apis.document.conf import Config


spec = APISpec(
        title="Document API",
        version="1.0.0",
        openapi_version="3.0.2",
        plugins=[
            FlaskPlugin(),
            MarshmallowPlugin(),
        ],
    )


class BigMemoryRequest(Request):
    max_content_length = 1024 * 1024 * 30
    max_form_memory_size = 1024 * 1024 * 30


def create_app(config_object=None):
    """
    FLASK_ENV=development FLASK_APP=apis.document.app flask run --port=5003
    """
    if config_object is None:
        config_object = Config
    app = Flask(__name__)
    app.request_class = BigMemoryRequest
    app.config.from_object(config_object)
    SENTRY_DSN = app.config.get("SENTRY_DSN")
    if SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
        sentry_sdk.init(SENTRY_DSN, integrations=[FlaskIntegration(), AwsLambdaIntegration()])
    app.register_blueprint(index.blueprint)
    app.register_blueprint(documents.blueprint)
    handlers.register(app)
    register_specs(app, spec, views=('document_post', 'document_fetch',))
    return app

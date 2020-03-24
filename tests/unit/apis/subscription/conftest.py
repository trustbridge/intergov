import pytest
from intergov.apis.subscriptions.app import create_app
from intergov.apis.subscriptions.conf import TestConfig


@pytest.yield_fixture(scope='session')
def app():
    yield create_app(TestConfig)

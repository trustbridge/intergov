import pytest
from intergov.apis.message.app import create_app
from intergov.apis.message.conf import TestConfig


@pytest.yield_fixture(scope='function')
def app():
    yield create_app(TestConfig)

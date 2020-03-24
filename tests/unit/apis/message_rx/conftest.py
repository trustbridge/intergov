import pytest
from intergov.apis.message_rx.app import create_app
from intergov.apis.message_rx.conf import TestConfig


@pytest.yield_fixture(scope='session')
def app():
    yield create_app(TestConfig)

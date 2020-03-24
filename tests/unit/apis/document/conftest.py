import pytest
from intergov.apis.document.app import create_app
from intergov.apis.document.conf import TestConfig


@pytest.yield_fixture(scope='function')
def app():
    yield create_app(TestConfig)

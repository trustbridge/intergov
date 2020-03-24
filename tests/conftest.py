# import os
# import tempfile
# import yaml
import pytest


@pytest.fixture(scope='session')
def docker_setup():
    return {
        'postgres': {
            'dbname': 'postgres_test',
            'user': 'intergovuser',
            'password': 'intergovpassword',
            'host': "postgresql"
        },
        'minio': {
            'access_key': 'minidemoaccess',
            'secret_key': 'miniodemosecret',
            'port': '9000',
            'host': "minio",
            'bucket': 'default',  # FIXME: should come from repo
            'use_ssl': False
        },
        'elasticmq': {
            'queue_name': 'test-queue-1',
            'use_ssl': False,
            'host': "elasticmq",
            'port': '9324',
            'context-path': '',
            'region': 'elasticmq',
            'access_key': 'x',
            'secret_key': 'x'
        }
    }


def pytest_addoption(parser):
    parser.addoption("--integration", action="store_true",
                     help="run integration tests")

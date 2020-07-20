from unittest import mock
import pytest
from intergov.conf import env_postgres_config
from intergov.repos.api_outbox.postgresrepo import PostgresRepo


TEST_CONFIG = env_postgres_config('TEST')


@mock.patch('intergov.repos.api_outbox.postgresrepo.TESTING', False)
def test_unsafe_methods_not_allowed():
    repo = PostgresRepo(TEST_CONFIG)
    with pytest.raises(RuntimeError):
        repo._unsafe_method__clear()


def test_unsafe_methods():
    repo = PostgresRepo(TEST_CONFIG)
    repo._unsafe_method__clear()
    assert repo.is_empty()

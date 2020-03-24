from unittest import mock
import pytest
from intergov.conf import env_postgres_config
from intergov.repos.api_outbox.postgresrepo import PostgresRepo


TEST_CONFIG = env_postgres_config('TEST')


@mock.patch('intergov.repos.api_outbox.postgresrepo.IGL_ALLOW_UNSAFE_REPO_CLEAR', False)
@mock.patch('intergov.repos.api_outbox.postgresrepo.IGL_ALLOW_UNSAFE_REPO_IS_EMPTY', False)
def test_unsafe_methods_not_allowed():
    repo = PostgresRepo(TEST_CONFIG)
    with pytest.raises(RuntimeError):
        repo._unsafe_clear_for_test()
    with pytest.raises(RuntimeError):
        repo._unsafe_is_empty_for_test()


def test_unsafe_methods():
    repo = PostgresRepo(TEST_CONFIG)
    repo._unsafe_clear_for_test()
    assert repo._unsafe_is_empty_for_test()

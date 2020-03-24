from intergov.conf import env_postgres_config
from intergov.repos.api_outbox import postgresrepo
from intergov.domain.wire_protocols import generic_discrete as gd
from tests.unit.domain.wire_protocols import test_generic_message as test_messages


def test_repository_delete_by_id_returns_truthy(
        docker_setup, pg_session):
    repo = postgresrepo.PostgresRepo(env_postgres_config('TEST'))
    msg_dict = test_messages._generate_msg_dict()
    msg = gd.Message.from_dict(msg_dict)
    msg_id = repo.post(msg)

    assert repo.delete(msg_id)
    assert not repo.delete(msg_id)

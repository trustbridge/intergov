from intergov.conf import env_postgres_config
from intergov.repos.api_outbox import postgresrepo
from intergov.domain.wire_protocols import generic_discrete as gd
from tests.unit.domain.wire_protocols import test_generic_message as test_messages


def test_repository_get_by_id(
        docker_setup, pg_session):
    repo = postgresrepo.PostgresRepo(env_postgres_config('TEST'))
    msg_dict = test_messages._generate_msg_dict()
    msg = gd.Message.from_dict(msg_dict)

    msg_id = repo.post(msg)
    msg2 = repo.get(msg_id)
    assert str(msg.sender) == str(msg2.sender)
    assert str(msg.receiver) == str(msg2.receiver)
    assert str(msg.subject) == str(msg2.subject)
    assert str(msg.obj) == str(msg2.obj)
    assert str(msg.predicate) == str(msg2.predicate)
    # never mind status, it's unlikely but possible that
    # a race condition could make them different
    assert not repo.get(-10)

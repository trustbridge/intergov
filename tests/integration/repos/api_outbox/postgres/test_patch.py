import pytest
from intergov.conf import env_postgres_config
from intergov.repos.api_outbox import postgresrepo
from intergov.domain.wire_protocols import generic_discrete as gd
from tests.unit.domain.wire_protocols import test_generic_message as test_messages


def test_repository_patch_status(
        docker_setup, pg_session):
    """
    Posting a message returns an integer

    The integer returned is a unique local ID of the message in the repo.
    """
    repo = postgresrepo.PostgresRepo(env_postgres_config('TEST'))

    # what is the statechart for api_outbox messages?
    for status in ('rejected', 'accepted'):
        msg_dict = test_messages._generate_msg_dict()
        msg = gd.Message.from_dict(msg_dict)
        msg_id = repo.post(msg)

        updates = {"status": status}
        assert repo.patch(msg_id, updates)
        assert not repo.patch(msg_id, updates)

        fetched_msg = repo.get(msg_id)
        assert fetched_msg.status == status

    with pytest.raises(Exception):
        repo.patch(msg_id, {'receiver': 'ES'})

    assert not repo.patch(msg_id, {'status': 'ahaha'})

    assert not repo.patch(-10, {'status': 'rejected'})

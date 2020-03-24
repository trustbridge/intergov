from intergov.conf import env_postgres_config
from intergov.repos.api_outbox import postgresrepo
from intergov.domain.wire_protocols import generic_discrete as gd
from tests.unit.domain.wire_protocols import test_generic_message as test_messages

CONF = env_postgres_config('TEST')

def test_repository_post_message_returns_an_integer(
        docker_setup, pg_session):
    """
    Posting a message returns an integer

    The integer returned is a unique local ID of the message in the repo.
    """
    repo = postgresrepo.PostgresRepo(CONF)
    msg_dict = test_messages._generate_msg_dict()
    msg = gd.Message.from_dict(msg_dict)
    assert isinstance(repo.post(msg), int)


def test_repository_post_message_rejects_duplicates(
        docker_setup, pg_session):
    '''
    Posting duplicate messages should fail

    (to, subject, predicate) is unique,
    among pending and accepted messages.
    '''
    repo = postgresrepo.PostgresRepo(CONF)
    msg_dict = test_messages._generate_msg_dict()
    msg = gd.Message.from_dict(msg_dict)

    m1 = repo.post(msg)
    assert m1 is not None  # first one should work
    assert repo.post(msg) is True  # the second post returns True due to no error but does nothing

    updates = {'status': 'rejected'}
    repo.patch(m1, updates)
    m2 = repo.post(msg)  # unless the first one was rejected
    assert m2

    # # now if we accept m2, we still can't post a 3rd one
    # updates = {'status': 'accepted'}
    # repo.patch(m2, updates)
    # assert not repo.post(msg)

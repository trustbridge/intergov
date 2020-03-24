from unittest import mock
import pytest
from intergov.repos.api_outbox.postgresrepo import PostgresRepo
from tests.unit.domain.wire_protocols.test_generic_message import (
    _generate_msg_object
)


CONNECTION_DATA = {
    'host': 'postgres.host',
    'user': 'postgres.user',
    'password': 'postgres.password',
    'dbname': 'postgres.dbname'
}


def _generate_message_mock(**kwargs):
    message_mock = mock.MagicMock()
    data = _generate_msg_object(**kwargs).to_dict()
    for key, value in data.items():
        setattr(message_mock, key, value)
    return message_mock


@mock.patch('intergov.repos.api_outbox.postgresrepo.create_engine', autospec=True)
def test_initialization(create_engine):
    # non default dbname
    PostgresRepo(CONNECTION_DATA)
    user = CONNECTION_DATA['user']
    password = CONNECTION_DATA['password']
    host = CONNECTION_DATA['host']
    dbname = CONNECTION_DATA['dbname']
    create_engine.assert_called_once_with(
        f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}"
    )
    create_engine.reset_mock()
    # default name
    dbname = 'postgres'
    connection_data = {**CONNECTION_DATA, 'dbname': None}
    PostgresRepo(connection_data)
    create_engine.assert_called_once_with(
        f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}"
    )
    # testing missing keys errors
    for key in CONNECTION_DATA.keys():
        connection_data = {**CONNECTION_DATA}
        del connection_data[key]
        with pytest.raises(KeyError) as einfo:
            PostgresRepo(connection_data)
        assert str(einfo.value) == str(KeyError(key))


@mock.patch('intergov.repos.api_outbox.postgresrepo.create_engine')
@mock.patch('intergov.repos.api_outbox.postgresrepo.sessionmaker')
def test_post(sessionmaker, create_engine):
    def session_add(m):
        m.id = 1

    query = mock.MagicMock()
    query.filter.return_value = query
    query.count.return_value = 0

    session = sessionmaker.return_value.return_value
    session.query.return_value = query
    session.add.side_effect = session_add

    repo = PostgresRepo(CONNECTION_DATA)
    # testing post
    message = _generate_msg_object()
    assert repo.post(message) is 1
    session.commit.assert_called_once()
    # testing duplicate
    query.count.return_value = 1
    assert repo.post(message) is True


@mock.patch('intergov.repos.api_outbox.postgresrepo.create_engine')
@mock.patch('intergov.repos.api_outbox.postgresrepo.sessionmaker')
def test_get(sessionmaker, create_engine):
    message = _generate_message_mock(sender_ref='xxxx-xxxx')

    def query_get(id):
        if id == 1:
            return message
        return None
    query = mock.MagicMock()
    query.get.side_effect = query_get
    session = sessionmaker.return_value.return_value
    session.query.return_value = query
    repo = PostgresRepo(CONNECTION_DATA)
    assert repo.get(1)
    assert not repo.get(2)


@mock.patch('intergov.repos.api_outbox.postgresrepo.create_engine')
@mock.patch('intergov.repos.api_outbox.postgresrepo.sessionmaker')
def test_patch(sessionmaker, create_engine):
    message = _generate_message_mock()
    message.id = 1

    def query_get(id):
        if id == 1:
            return message
        return None

    query = mock.MagicMock()
    query.get.side_effect = query_get
    session = sessionmaker.return_value.return_value
    session.query.return_value = query
    repo = PostgresRepo(CONNECTION_DATA)
    # only status can be patched
    with pytest.raises(Exception):
        repo.patch(1, {'sender': 'AU'})
    # status only in ['accepted', 'rejected', 'sending']
    assert not repo.patch(1, {'status': 'abrakadabra'})
    # patching correct statuses
    for status in ['sending', 'rejected', 'accepted']:
        message.status = 'pending'
        assert repo.patch(1, {'status': status})
        assert message.status == status
        session.commit.assert_called_once()
        session.reset_mock()
    # non existing message
    assert not repo.patch(2, {'status': 'accepted'})
    # final status
    for status in ['rejected', 'accepted']:
        message.status = status
        assert not repo.patch(1, {'status': 'sending'})
        assert message.status == status
        session.commit.assert_not_called()
        session.reset_mock()


@mock.patch('intergov.repos.api_outbox.postgresrepo.create_engine')
@mock.patch('intergov.repos.api_outbox.postgresrepo.sessionmaker')
def test_delete(sessionmaker, create_engine):
    message = _generate_message_mock()
    message.id = 1

    def query_get(id):
        if id == 1:
            return message
        return None

    query = mock.MagicMock()
    query.get.side_effect = query_get
    session = sessionmaker.return_value.return_value
    session.query.return_value = query
    repo = PostgresRepo(CONNECTION_DATA)
    # deleting non existing message
    assert not repo.delete(2)
    # deleting existing message
    assert repo.delete(1)
    session.delete.assert_called_once_with(message)
    session.commit.assert_called_once()


@mock.patch('intergov.repos.api_outbox.postgresrepo.create_engine')
@mock.patch('intergov.repos.api_outbox.postgresrepo.sessionmaker')
def test_get_next_pending_message(sessionmaker, create_engine):
    message = _generate_message_mock()
    message.id = 1
    query = mock.MagicMock()
    query.filter.return_value = query
    query.first.side_effect = [
        message,
        Exception()
    ]
    session = sessionmaker.return_value.return_value
    session.query.return_value = query
    repo = PostgresRepo(CONNECTION_DATA)
    assert repo.get_next_pending_message() == message
    assert not repo.get_next_pending_message()


@mock.patch('intergov.repos.api_outbox.postgresrepo.create_engine')
@mock.patch('intergov.repos.api_outbox.postgresrepo.sessionmaker')
def test_search(sessionmaker, create_engine):
    message = _generate_message_mock()
    message.id = 1
    query = mock.MagicMock()
    query.filter.return_value = query
    query.all.return_value = [message]
    session = sessionmaker.return_value.return_value
    session.query.return_value = query
    repo = PostgresRepo(CONNECTION_DATA)
    for filter_key in {
        'sender__eq',
        'receiver__eq',
        'subject__eq',
        'object__eq',
        'predicate__eq',
        'predicate__wild'
    }:
        assert len(repo.search({filter_key: 'value'})) == 1
        query.filter.assert_called()
        query.all.assert_called_once()
        sessionmaker.reset_mock()
    assert len(repo.search()) == 1


@mock.patch('intergov.repos.api_outbox.postgresrepo.IGL_ALLOW_UNSAFE_REPO_CLEAR', False)
@mock.patch('intergov.repos.api_outbox.postgresrepo.IGL_ALLOW_UNSAFE_REPO_IS_EMPTY', False)
@mock.patch('intergov.repos.api_outbox.postgresrepo.create_engine')
@mock.patch('intergov.repos.api_outbox.postgresrepo.sessionmaker')
def test_unsafe_not_allowed(sessionmaker, create_engine):
    repo = PostgresRepo(CONNECTION_DATA)
    with pytest.raises(RuntimeError):
        repo._unsafe_clear_for_test()
    with pytest.raises(RuntimeError):
        repo._unsafe_is_empty_for_test()


@mock.patch('intergov.repos.api_outbox.postgresrepo.IGL_ALLOW_UNSAFE_REPO_CLEAR', True)
@mock.patch('intergov.repos.api_outbox.postgresrepo.IGL_ALLOW_UNSAFE_REPO_IS_EMPTY', True)
@mock.patch('intergov.repos.api_outbox.postgresrepo.create_engine')
@mock.patch('intergov.repos.api_outbox.postgresrepo.sessionmaker')
def test_unsafe(sessionmaker, create_engine):
    query = mock.MagicMock()
    query.count.return_value = 0
    session = sessionmaker.return_value.return_value
    session.query.return_value = query
    repo = PostgresRepo(CONNECTION_DATA)

    repo._unsafe_clear_for_test()
    query.delete.assert_called_once()
    session.commit.assert_called_once()
    sessionmaker.reset_mock()

    query.delete.side_effect = Exception()
    repo._unsafe_clear_for_test()
    session.close.assert_called_once()
    query.delete.assert_called_once()
    sessionmaker.reset_mock()

    assert repo._unsafe_is_empty_for_test()
    query.count.return_value = 10
    assert not repo._unsafe_is_empty_for_test()
    sessionmaker.reset_mock()

    query.count.side_effect = Exception()
    repo._unsafe_is_empty_for_test()
    query.count.assert_called_once()
    session.close.assert_called_once()

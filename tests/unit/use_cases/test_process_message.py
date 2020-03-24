import pytest
from unittest import mock

from intergov.domain.wire_protocols import generic_discrete as protocol
from intergov.domain.country import Country
from intergov.use_cases import ProcessMessageUseCase
from tests.unit.domain.wire_protocols import test_generic_message as test_protocol


@pytest.fixture
def valid_message_dicts():
    out = []
    for i in range(1):
        out.append(
            test_protocol._generate_msg_dict())
    return out


def test_empty_inbox(valid_message_dicts):
    bc_inbox = mock.Mock()
    bc_inbox.get.return_value = None
    message_lake = mock.Mock()
    object_acl = mock.Mock()
    object_retreival = mock.Mock()
    notifications = mock.Mock()
    use_case = ProcessMessageUseCase(
        'AU',
        bc_inbox,
        message_lake,
        object_acl,
        object_retreival,
        notifications,
        None  # this is blockchain repo which won't be used now
    )

    assert not use_case.execute()  # returns False
    assert not message_lake.post.called
    assert not object_acl.post.called
    assert not object_retreival.post.called
    assert not notifications.post.called
    assert not bc_inbox.delete.called


def test_non_empty_inbox(valid_message_dicts):
    message_dict = valid_message_dicts[0]
    message_dict['status'] = 'received'
    m = protocol.Message.from_dict(message_dict)
    bc_inbox = mock.Mock()
    bc_inbox.get.return_value = (432, m)
    message_lake = mock.Mock()
    object_acl = mock.Mock()
    object_retreival = mock.Mock()
    notifications = mock.Mock()
    use_case = ProcessMessageUseCase(
        'CN',
        bc_inbox,
        message_lake,
        object_acl,
        object_retreival,
        notifications,
        None  # this is blockchain repo which won't be used now
    )

    assert use_case.execute()
    assert message_lake.post.called
    assert object_acl.post.called
    assert object_retreival.post_job.called
    assert notifications.post.called
    assert bc_inbox.delete.called


def test_repo_exceptions(valid_message_dicts):

    message_dict = valid_message_dicts[0]
    message_dict['status'] = 'pending'
    m = protocol.Message.from_dict(message_dict)

    bc_inbox = mock.Mock()
    bc_inbox.get.return_value = (432, m)
    message_lake = mock.Mock()
    object_acl = mock.Mock()
    object_retreival = mock.Mock()
    notifications = mock.Mock()
    message_lake = mock.Mock()
    object_acl = mock.Mock()
    object_retreival = mock.Mock()
    notifications = mock.Mock()
    blockchain_outbox = mock.Mock()

    use_case = ProcessMessageUseCase(
        'CN',
        bc_inbox,
        message_lake,
        object_acl,
        object_retreival,
        notifications,
        blockchain_outbox
    )

    for repo_method, message_status in {
        message_lake.post: 'received',
        object_acl.post: 'received',
        notifications.post: 'received',
        blockchain_outbox.post: 'pending',
        object_retreival.post_job: 'received'
    }.items():
        m.status = message_status
        repo_method.reset_mock()
        repo_method.side_effect = Exception()
        assert not use_case.execute()
        repo_method.assert_called()
        repo_method.side_effect = None

    # test loopback, it's ok, we just don't post it to object_retreval_repo
    m.sender = 'CN'
    assert use_case.execute()

import pytest
from unittest import mock
import uuid

from intergov.domain.wire_protocols import generic_discrete as protocol
from intergov.use_cases import EnqueueMessageUseCase
from tests.unit.domain.wire_protocols import test_generic_message as test_protocol


@pytest.fixture
def valid_message_dicts():
    out = []
    for i in range(9):
        out.append(
            test_protocol._generate_msg_dict())
    return out


def test_enque_true_if_message_valid(valid_message_dicts):
    inbox = mock.Mock()
    inbox.post.return_value = True
    m_dict = valid_message_dicts[0]
    m_dict["sender_ref"] = uuid.uuid4()
    m = protocol.Message.from_dict(m_dict)
    use_case = EnqueueMessageUseCase(inbox)
    assert use_case.execute(m)


def test_enque_false_if_inbox_rejects_message(valid_message_dicts):
    inbox = mock.Mock()
    inbox.post.return_value = False
    m_dict = valid_message_dicts[0]
    m_dict["sender_ref"] = uuid.uuid4()
    m = protocol.Message.from_dict(m_dict)
    use_case = EnqueueMessageUseCase(inbox)
    assert not use_case.execute(m)


def test_enque_false_if_message_invalid_subject(valid_message_dicts):
    inbox = mock.Mock()
    inbox.post.return_value = False
    m_dict = valid_message_dicts[0]
    m_dict["sender_ref"] = uuid.uuid4()
    m_dict["subject"] = None  # Oop, invalid
    m = protocol.Message.from_dict(m_dict)
    use_case = EnqueueMessageUseCase(inbox)
    with pytest.raises(Exception) as e:
        use_case.execute(m)
        assert str(e) == "can't enqueue invalid message"


def test_enque_false_if_message_invalid_object(valid_message_dicts):
    inbox = mock.Mock()
    inbox.post.return_value = False
    m_dict = valid_message_dicts[0]
    m_dict["sender_ref"] = uuid.uuid4()
    m_dict["object"] = None  # Oop, invalid
    m = protocol.Message.from_dict(m_dict)
    use_case = EnqueueMessageUseCase(inbox)
    assert not use_case.execute(m)


def test_enque_false_if_message_invalid_predicate(valid_message_dicts):
    inbox = mock.Mock()
    inbox.post.return_value = False
    m_dict = valid_message_dicts[0]
    m_dict["sender_ref"] = uuid.uuid4()
    m_dict["predicate"] = None  # Oop, invalid
    m = protocol.Message.from_dict(m_dict)
    use_case = EnqueueMessageUseCase(inbox)
    with pytest.raises(Exception) as e:
        use_case.execute(m)
        assert str(e) == "can't enqueue invalid message"


def test_enque_false_if_message_without_sender_ref(valid_message_dicts):
    inbox = mock.Mock()
    inbox.post.return_value = False
    m_dict = valid_message_dicts[0]
    # m_dict["sender_ref"] = uuid.uuid4()
    # del m_dict["sender_ref"]

    m = protocol.Message.from_dict(m_dict)
    use_case = EnqueueMessageUseCase(inbox)
    with pytest.raises(Exception):
        use_case.execute(m)

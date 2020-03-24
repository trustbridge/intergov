import pytest
from unittest import mock

from intergov.domain.wire_protocols import generic_discrete as protocol
from intergov.use_cases import post_message_use_case as uc
from tests.unit.domain.wire_protocols import test_generic_message as test_protocol


@pytest.fixture
def valid_message_dicts():
    out = []
    for i in range(9):
        out.append(
            test_protocol._generate_msg_dict())
    return out


def test_post_valid_messages_returns_true(valid_message_dicts):
    channel = mock.Mock()
    channel.post.return_value = True
    channel.message_factory.return_value = protocol.Message

    messages = [protocol.Message.from_dict(m) for m in valid_message_dicts]
    for msg in messages:
        use_case = uc.PostMessageUseCase(msg, channel)
        assert use_case.execute() is not None
        # TODO: what else shows us the use_case execution worked?

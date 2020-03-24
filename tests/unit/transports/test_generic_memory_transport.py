import pytest

from intergov.domain.wire_protocols import generic_discrete as gd
from intergov.transports import generic_memory as gm
from tests.unit.domain.wire_protocols import test_generic_message as tgm


@pytest.fixture
def valid_message_dicts():
    out = []
    for i in range(9):
        out.append(
            tgm._generate_msg_dict())
    return out


def test_generic_memory_transport_get_messages(valid_message_dicts):
    messages = [gd.Message.from_dict(msg) for msg in valid_message_dicts]
    transport = gm.GenericMemoryTransport(valid_message_dicts)
    assert transport.get_messages() == messages


def test_generic_memory_transport_post_message(valid_message_dicts):
    transport = gm.GenericMemoryTransport()  # empty
    for msg in [gd.Message.from_dict(msg) for msg in valid_message_dicts]:
        transport.post_message(msg)
        assert msg in transport.get_messages()

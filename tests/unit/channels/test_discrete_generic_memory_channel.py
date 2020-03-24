from intergov.channels import discrete_generic_memory as channels
from intergov.domain.wire_protocols import generic_discrete as proto
from tests.unit.domain.wire_protocols import test_generic_message as proto_tests


def test_message_factory():
    chan = channels.DiscreteGenericMemoryChannel()
    MessageClass = chan.message_factory()
    msg_dict = proto_tests._generate_msg_dict()
    msg = MessageClass.from_dict(msg_dict)

    assert isinstance(msg, proto.Message)


def test_post():
    chan = channels.DiscreteGenericMemoryChannel()
    MessageClass = chan.message_factory()
    msg_dict = proto_tests._generate_msg_dict()
    msg = MessageClass.from_dict(msg_dict)

    chan.post_message(msg)
    assert msg in chan.get_messages()

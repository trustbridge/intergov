from intergov.use_cases import get_message_list as uc
from intergov.domain.channel_filters.none_filter import NoneFilter
from intergov.domain.wire_protocols import generic_discrete as protocol
from tests.unit.domain.wire_protocols import test_generic_message as test_protocol


class MockChannel:
    def __init__(self):
        self.valid_messages = []
        for i in range(9):
            self.valid_messages.append(
                protocol.Message.from_dict(
                    test_protocol._generate_msg_dict()))

    def get_messages(self, channel_filter):
        out = []
        for msg in self.valid_messages:
            if not channel_filter.screen_message(msg):
                out.append(msg)
        return out


def test_get_message_list_returns_valid_messages():
    channel = MockChannel()
    channel_filter = NoneFilter()
    use_case = uc.GetMessageListUseCase(channel, channel_filter)
    result = use_case.execute()
    for msg in result:
        assert msg.is_valid()

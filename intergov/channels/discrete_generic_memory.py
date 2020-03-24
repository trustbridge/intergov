from intergov.transports import generic_memory as transport
from intergov.domain.wire_protocols import generic_discrete as protocol
from intergov.domain.channel_filters import none_filter as filters


class DiscreteGenericMemoryChannel:

    ID = 'DiscreteGenericMemoryChannel'

    def __init__(self):
        self.transport = transport.GenericMemoryTransport()
        self.message_class = protocol.Message
        self.channel_filter = filters.NoneFilter()

    def message_factory(self):
        return self.message_class

    def post_message(self, message):
        return self.transport.post_message(message, self.channel_filter)

    def get_messages(self):
        return self.transport.get_messages(self.channel_filter)

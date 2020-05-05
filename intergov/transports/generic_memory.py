from intergov.domain.wire_protocols import generic_discrete as gd


class GenericMemoryTransport:
    def __init__(self, data=None):
        if data:
            self.data = data
        else:
            self.data = []

    def get_messages(self, channel_filter=None):
        out = []
        for adict in self.data:
            msg = gd.Message.from_dict(adict)
            if channel_filter:
                if not channel_filter.screen_message(msg):
                    out.append(msg)
            else:
                out.append(msg)
        return out

    def post_message(self, msg, channel_filter=None):
        if channel_filter:
            if channel_filter.screen_message(msg):
                return False
        assert isinstance(msg, gd.Message), msg.__class__
        if not msg.is_valid():
            return False
        datum = msg.to_dict()
        if datum not in self.data:
            self.data.append(datum)
        return True

# Warning: not used, but tested


class GetMessageListUseCase:

    def __init__(self, channel, channel_filter):
        self.channel_filter = channel_filter
        self.channel = channel

    def execute(self):
        return self.channel.get_messages(self.channel_filter)

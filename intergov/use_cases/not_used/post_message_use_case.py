class PostMessageUseCase:

    def __init__(self, message, channel):
        self.message = message
        self.channel = channel

    def execute(self):
        if not self.message.is_valid():
            return None

        return self.channel.post_message(self.message)

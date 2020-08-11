# Warning: not used


class PostMessageToAPIInboxUseCase:
    """
    Is called by a blockchain listener
    Receives incoming message (from the remote jurisdiction) and
    ensures that this message is handled somehow
    """

    def __init__(self, api_inbox_repo):
        self.api_inbox = api_inbox_repo

    def execute(self, message):
        if not message.is_valid():
            return False

        return self.api_inbox.post_message(message)
        # if not posted:
        #     return posted  # post should return a referrer_id
        # else:
        #     return True

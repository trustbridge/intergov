# Warning: not used yet, but already has some tests


class EnqueuePostedMessageUseCase:
    """
    TODO: specify what this task does and how is it different
    from the EnqueueMessageUseCase (which is quite unversal) and
    PostMessageUseCase

    now it just gets messages from inbox and puts them to outbox,
    which is strange, given inbox is for incoming messages and outbox
    for the generated ones. So it looks like we just fire message back
    instead of processing it.
    """

    def __init__(self, api_inbox_repo, api_outbox_repo):
        self.inbox = api_inbox_repo
        self.outbox = api_outbox_repo

    def execute(self):
        # this waits for a short time if none available,
        # and returns None if none still available
        gotten = self.inbox.get()
        if not gotten:
            # so we give up
            return False
        else:
            (msg_id, message) = gotten
            if self.outbox.post(message):
                self.inbox.delete(msg_id)
                return True
            else:
                # post failed, someone can retry later
                # or eventually let it pass through to the dead letter queue
                return False

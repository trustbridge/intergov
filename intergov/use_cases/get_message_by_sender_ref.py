from intergov.monitoring import statsd_timer


class GetMessageBySenderRefUseCase:
    """
    Used by the message retrieve endpoint

    Receive the msg_id which is the string like:
    {sender}:{sender_ref}
    and return the message object (parsed, with status and other fields)
    """

    def __init__(self, message_lake_repo):
        self.message_lake = message_lake_repo

    @statsd_timer("usecase.GetMessageBySenderRefUseCase.execute")
    def execute(self, sender_ref):
        assert ':' in sender_ref, "sender_ref must be in format AU:XXXX, where AU is a sender"
        sender, sender_ref = sender_ref.split(':', maxsplit=1)
        found = self.message_lake.get(sender, sender_ref)
        if not found:
            return False
        else:
            return found

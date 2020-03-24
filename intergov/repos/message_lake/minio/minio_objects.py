
class Message():
    """
    The minio message repository object

    this should be serialised using serializer.generic_discrete_message.py
    """
    def __init__(
            self, sender, receiver,
            subject, obj, predicate,
            status=None, sender_ref=None):
        self.sender = sender
        self.receiver = receiver
        self.subject = subject
        self.obj = obj
        self.predicate = predicate
        self.status = status
        self.sender_ref = None


class Message():
    """
    The minio message repository object

    how should this be serialised:
    * json?
    * messagepack?
    * bson?
    * cbor?
    * pickle?
    """
    def __init__(
            self, sender, receiver,
            subject, obj, predicate,
            status=None):
        self.sender = sender
        self.receiver = receiver
        self.subject = subject
        self.obj = obj
        self.predicate = predicate
        self.status = status

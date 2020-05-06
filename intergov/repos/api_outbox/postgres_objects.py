from sqlalchemy import Column, Integer, String  # , Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Message(Base):
    """
    The postgres message repository object

    Inherits a convenient query interface
    from the SQLAlchemy "declarative_base",
    which powers the implementation of the
    postgresrepo.
    """
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True)
    sender = Column(String(16), nullable=False)
    receiver = Column(String(16), nullable=False)
    subject = Column(String(2048), nullable=False)
    obj = Column(String(256), nullable=False)
    predicate = Column(String(512), nullable=False)
    sender_ref = Column(String(256), nullable=False)

    # outbox: pending, accepted, rejected
    # bc: block depth? block number?
    status = Column(String(12), default="accepted")

    def __str__(self):
        return self.subject

    def to_dict(self):
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'subject': self.subject,
            'obj': self.obj,
            'predicate': self.predicate,
            'sender_ref': self.sender_ref,
            'status': self.status,
        }

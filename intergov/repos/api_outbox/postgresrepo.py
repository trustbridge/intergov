from libtrustbridge.utils.conf import TESTING
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

from intergov.domain.wire_protocols import generic_discrete as message
from intergov.loggers import logging
from intergov.repos.api_outbox.postgres_objects import Base, Message

logger = logging.getLogger(__name__)


class PostgresRepo:
    """
    https://docs.sqlalchemy.org/en/13/orm/query.html
    http://www.leeladharan.com/sqlalchemy-query-with-or-and-like-common-filters
    """

    DEFAULT_DB = 'postgres'

    def __init__(self, connection_data):
        connection_string = "postgresql+psycopg2://{}:{}@{}/{}".format(
            connection_data['user'],
            connection_data['password'],
            connection_data['host'],
            connection_data['dbname'] or self.DEFAULT_DB
        )
        self.engine = create_engine(
            connection_string,
        )
        # echo=True  # use this for debugging
        Base.metadata.bind = self.engine
        Base.metadata.create_all()

    def _create_message_objects(self, results):
        return [
            message.Message(
                sender=q.sender,
                receiver=q.receiver,
                subject=q.subject,
                obj=q.obj,
                predicate=q.predicate,
                sender_ref=q.sender_ref,
                status=q.status)
            for q in results
        ]

    def post(self, msg):
        DBSession = sessionmaker(bind=self.engine)
        result = True
        try:
            session = DBSession()

            # need to convert from domain message to PG message
            sender = str(msg.sender)
            receiver = str(msg.receiver)
            subject = str(msg.subject)
            obj = str(msg.obj)
            predicate = str(msg.predicate)
            sender_ref = str(msg.sender_ref)

            # but not if it would create a duplicate
            dupes_query = session.query(Message).filter(
                Message.sender == sender,
                Message.sender_ref == sender_ref,
                Message.receiver == receiver,
                Message.subject == subject,
                Message.obj == obj,
                Message.predicate == predicate,
                Message.status != 'rejected'
            )

            if dupes_query.count() == 0:
                m = Message(
                    sender=sender,
                    receiver=receiver,
                    subject=subject,
                    obj=obj,
                    predicate=predicate,
                    sender_ref=sender_ref,
                    status='pending'
                )

                session.add(m)
                session.flush()
                result = m.id
                session.commit()
        finally:
            session.close()
        return result

    def patch(self, msg_id, updates):
        # is there anything else that should be patchable?
        for k in updates.keys():
            if k != "status":
                raise Exception("only status can be patched at this time")

        new_status = updates["status"]

        if new_status not in ('sending', 'rejected', 'accepted'):
            return False

        DBSession = sessionmaker(bind=self.engine)
        session = DBSession()
        msg = session.query(Message).get(msg_id)
        if not msg:
            session.close()
            return False

        if msg.status in ('rejected', 'accepted'):
            session.close()
            return False

        msg.status = new_status
        session.flush()
        session.commit()
        session.close()
        return True

    def delete(self, msg_id):
        DBSession = sessionmaker(bind=self.engine)
        session = DBSession()
        msg = session.query(Message).get(msg_id)

        if not msg:
            session.close()
            return False

        session.delete(msg)
        session.flush()
        session.commit()
        session.close()
        return True

    def get(self, msg_id):
        DBSession = sessionmaker(bind=self.engine)
        session = DBSession()
        found = session.query(Message).get(msg_id)

        if found is None:
            session.close()
            return False

        session.close()
        return self._create_message_objects([found])[0]

    def search(self, filters=None):
        DBSession = sessionmaker(bind=self.engine)
        session = DBSession()
        query = session.query(Message)

        if filters is None:
            return self._create_message_objects(query.all())

        if 'sender__eq' in filters:
            query = query.filter(
                Message.sender == filters['sender__eq'])
        if 'receiver__eq' in filters:
            query = query.filter(
                Message.receiver == filters['receiver__eq'])
        if 'subject__eq' in filters:
            query = query.filter(
                Message.subject == filters['subject__eq'])
        if 'object__eq' in filters:
            query = query.filter(
                Message.obj == filters['object__eq'])
        if 'predicate__eq' in filters:
            query = query.filter(
                Message.predicate == filters['predicate__eq'])
        if 'predicate__wild' in filters:
            # Predicate__wild is interpreted as a
            # left-bounded deterministic regex, e.g. "foo.*"
            # We accept it with or without the trailing '.'
            w = filters['predicate__wild']
            if str(w)[-1] is not str('.'):
                w = "{}.".format(w)
            query = query.filter(
                Message.predicate.like(
                    "{}%".format(w)))

        output = self._create_message_objects(query.all())
        session.close()
        return output

    def get_next_pending_message(self):
        try:
            DBSession = sessionmaker(bind=self.engine)
            session = DBSession()
            return session.query(Message).filter(
                or_(
                    Message.status == 'pending',
                    # we should query for that status only if no more
                    # workers are active, of it the message has this status for
                    # quite some time (worker died)
                    Message.status == 'sending',
                )
            ).first()
        except Exception as e:
            logger.exception(e)
            return None
        finally:
            session.close()

    # primarily for testing purposes
    # do not use in production code
    def _unsafe_method__clear(self):
        if not TESTING:
            raise RuntimeError(
                'repo._unsafe_method__clear method allowed only when env TESTING=True'
            )
        DBSession = sessionmaker(bind=self.engine)
        session = DBSession()
        try:
            session.query(Message).delete()
            session.commit()
        except Exception as e:
            logger.exception(e)
            session.rollback()
        finally:
            session.close()

    def is_empty(self):
        DBSession = sessionmaker(bind=self.engine)
        session = DBSession()
        count = None
        try:
            count = session.query(Message).count()
        except Exception as e:
            logger.exception(e)
        finally:
            session.close()
        return count == 0

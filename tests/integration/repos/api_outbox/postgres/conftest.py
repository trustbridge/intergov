import psycopg2
import sqlalchemy
import sqlalchemy_utils
import pytest
from intergov.conf import env_postgres_config
from intergov.repos.api_outbox.postgres_objects import Base, Message
from tests.unit.domain.wire_protocols import test_generic_message as test_messages


def pg_is_responsive(ip, docker_setup):
    try:
        conn = psycopg2.connect(
            "host={} user={} password={} dbname={}".format(
                ip,
                docker_setup['postgres']['user'],
                docker_setup['postgres']['password'],
                'postgres'
            )
        )
        conn.close()
        return True
    except psycopg2.OperationalError:
        return False


@pytest.fixture(scope='session')
def pg_engine(docker_setup):
    # docker_services.wait_until_responsive(
    #     timeout=30.0, pause=0.1,
    #     check=lambda: pg_is_responsive("postgresql", docker_setup)
    # )
    conf = env_postgres_config('TEST')
    conn_str = "postgresql+psycopg2://{}:{}@{}/{}".format(
        conf['user'],
        conf['password'],
        conf['host'],
        conf['dbname']
    )
    engine = sqlalchemy.create_engine(conn_str)
    if not sqlalchemy_utils.database_exists(engine.url):
        sqlalchemy_utils.create_database(engine.url)
    conn = engine.connect()
    yield engine
    conn.close()


@pytest.fixture(scope='session')
def pg_session_empty(pg_engine):
    Base.metadata.create_all(pg_engine)
    Base.metadata.bind = pg_engine
    DBSession = sqlalchemy.orm.sessionmaker(bind=pg_engine)
    session = DBSession()
    yield session
    session.close()


@pytest.fixture(scope='function')
def pg_data():
    return [test_messages._generate_msg_dict() for x in range(9)]


@pytest.fixture(scope='function')
def pg_session(pg_session_empty, pg_data):
    for m in pg_data:
        new_msg = Message(
            sender=m["sender"],
            receiver=m["receiver"],
            subject=m["subject"],
            obj=m["obj"],
            predicate=m["predicate"],
            sender_ref=m.get('sender_ref') or 'random-sender-ref'
        )

        pg_session_empty.add(new_msg)
        pg_session_empty.commit()
    yield pg_session_empty
    pg_session_empty.query(Message).delete()

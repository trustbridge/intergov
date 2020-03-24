import logging

import pytest
from minio import Minio

from intergov.repos.base.minio.minio_objects import Message
from tests.unit.domain.wire_protocols import test_generic_message as test_messages


def minio_is_responsive(docker_setup):
    try:
        mc = Minio(
            '{}:{}'.format(
                docker_setup['minio']['host'],
                docker_setup['minio']['port']),
            access_key=docker_setup['minio']['access_key'],
            secret_key=docker_setup['minio']['secret_key'],
            secure=docker_setup['minio']['use_ssl'])
        mc.list_buckets()
        return True
    except Exception as e:  # except what?
        logging.exception(e)
        return False


@pytest.fixture(scope='session')
def minio_client(docker_setup):
    # docker_services.wait_until_responsive(
    #     timeout=30.0, pause=0.1,
    #     check=lambda: minio_is_responsive(docker_setup)
    # )
    mc = Minio(
        '{}:{}'.format(
            docker_setup['minio']['host'],
            docker_setup['minio']['port']),
        access_key=docker_setup['minio']['access_key'],
        secret_key=docker_setup['minio']['secret_key'],
        secure=docker_setup['minio']['use_ssl'])
    yield mc


@pytest.fixture(scope='function')
def minio_data():
    return [test_messages._generate_msg_dict() for x in range(9)]


@pytest.fixture(scope='function')
def minio_session(minio_client, minio_data):
    for m in minio_data:
        new_msg = Message(
            sender=m["sender"],
            receiver=m["receiver"],
            subject=m["subject"],
            obj=m["obj"],  # ugh! FIXME
            predicate=m["predicate"])
        # FIXME: add each thing to the repo
        # minio_client.add(new_msg)
        print(new_msg)
    yield minio_client
    # FIXME: delete everything in the repo

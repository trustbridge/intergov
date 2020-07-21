from libtrustbridge.domain.wire_protocols.generic_discrete import Message
from libtrustbridge.repos.elasticmqrepo import ElasticMQRepo

from tests.unit.domain.wire_protocols import test_generic_message

REPO_CLASS = ElasticMQRepo


def test_repository_post_returns_truithy(
        docker_setup,
        elasticmq_client):
    repo = REPO_CLASS(docker_setup['elasticmq'])
    msg_dict = test_generic_message._generate_msg_dict()
    msg = Message.from_dict(msg_dict)
    assert repo.post(msg)


def test_elasticmq_post_creates_a_message(
        docker_setup,
        elasticmq_client):
    repo = REPO_CLASS(docker_setup['elasticmq'])
    msg_dict = test_generic_message._generate_msg_dict()
    msg = Message.from_dict(msg_dict)
    elasticmq_client.purge_queue(QueueUrl=repo.queue_url)
    assert not repo.get()
    assert repo.post(msg)
    assert repo.get()


def test_elasticmq_get_returns_a_message_and_id(
        docker_setup,
        elasticmq_client):
    repo = REPO_CLASS(docker_setup['elasticmq'])
    msg_dict = test_generic_message._generate_msg_dict()
    msg = Message.from_dict(msg_dict)

    elasticmq_client.purge_queue(QueueUrl=repo.queue_url)
    assert repo.post(msg)
    msg_id, msg = repo.get()
    assert isinstance(msg, Message)


def test_elasticmq_delete_actually_does(
        docker_setup,
        elasticmq_client):
    repo = REPO_CLASS(docker_setup['elasticmq'])
    msg_dict = test_generic_message._generate_msg_dict()
    msg = Message.from_dict(msg_dict)

    elasticmq_client.purge_queue(QueueUrl=repo.queue_url)
    assert repo.post(msg)
    msg_id, msg = repo.get()
    assert repo.delete(msg_id)
    assert not repo.get()


def test_elasticmq_clear(docker_setup):
    repo = REPO_CLASS(docker_setup['elasticmq'])
    message = Message.from_dict(test_generic_message._generate_msg_dict())
    assert repo.post(message)
    assert repo.post(message)
    repo._unsafe_method__clear()
    assert not repo.get()


def test_elasticmq_post_after_clear(docker_setup):
    repo = REPO_CLASS(docker_setup['elasticmq'])
    for i in range(5):
        message = Message.from_dict(test_generic_message._generate_msg_dict())
        repo._unsafe_method__clear()
        assert repo.post(message)
        assert repo.get()

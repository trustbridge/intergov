from unittest import mock
import json
import pytest
from intergov.repos.base.elasticmq.elasticmqrepo import ElasticMQRepo
from tests.unit.domain.wire_protocols.test_generic_message import (
    _generate_msg_object
)

REQUIRED_CONNECTION_KEYS = [
    'queue_name',
    'host',
    'port',
    'secret_key',
    'access_key'
]


CONNECTION_DATA = {
    'host': 'elasticmq.host',
    'port': 1000,
    'access_key': 'access_key',
    'secret_key': 'secret_key',
    'queue_name': 'queue_name',
    'use_ssl': False,
    'region': 'region'
}


AWS_CONNECTION_DATA = {
    'endpoint_url': f"http://{CONNECTION_DATA['host']}:{CONNECTION_DATA['port']}/",
    'region_name': CONNECTION_DATA['region'],
    'aws_access_key_id': CONNECTION_DATA['access_key'],
    'aws_secret_access_key': CONNECTION_DATA['secret_key'],
    'use_ssl': CONNECTION_DATA['use_ssl']
}


CONNECTION_DATA_SSL = {
    **CONNECTION_DATA,
    'use_ssl': True
}


AWS_CONNECTION_DATA_SSL = {
    'endpoint_url': f"https://{CONNECTION_DATA_SSL['host']}:{CONNECTION_DATA_SSL['port']}/",
    'region_name': CONNECTION_DATA_SSL['region'],
    'aws_access_key_id': CONNECTION_DATA_SSL['access_key'],
    'aws_secret_access_key': CONNECTION_DATA_SSL['secret_key'],
    'use_ssl': CONNECTION_DATA_SSL['use_ssl']
}

QUEUE_URL = 'test_queue_url'


def test_aws_connection_args():
    assert ElasticMQRepo._aws_connection_data(CONNECTION_DATA) == AWS_CONNECTION_DATA
    assert ElasticMQRepo._aws_connection_data(CONNECTION_DATA_SSL) == AWS_CONNECTION_DATA_SSL


@mock.patch('intergov.repos.base.elasticmq.elasticmqrepo.boto3', autospec=True)
def test_initialization(boto3):
    for key in REQUIRED_CONNECTION_KEYS:
        connection_data = {**CONNECTION_DATA}
        del connection_data[key]
        with pytest.raises(KeyError) as einfo:
            ElasticMQRepo(connection_data)
        assert str(einfo.value) == str(KeyError(key))

    sqs_client = boto3.client.return_value

    # testing non ssl connection
    ElasticMQRepo(CONNECTION_DATA)
    boto3.client.assert_called_once_with('sqs', **AWS_CONNECTION_DATA)
    sqs_client.get_queue_url.assert_called_once_with(QueueName=CONNECTION_DATA['queue_name'])
    boto3.reset_mock()

    # testing ssl connection
    ElasticMQRepo(CONNECTION_DATA_SSL)
    boto3.client.assert_called_once_with('sqs', **AWS_CONNECTION_DATA_SSL)
    sqs_client.get_queue_url.assert_called_once_with(QueueName=CONNECTION_DATA['queue_name'])
    boto3.reset_mock()

    class DefaultQueueNameRepo(ElasticMQRepo):

        def _get_queue_name(self):
            return 'default_queue_name'

    # testing default queue name
    connection_data = {**CONNECTION_DATA}
    del connection_data['queue_name']
    DefaultQueueNameRepo(connection_data)
    boto3.client.assert_called_once_with('sqs', **AWS_CONNECTION_DATA)
    sqs_client.get_queue_url.assert_called_once_with(QueueName='default_queue_name')
    boto3.reset_mock()


@mock.patch('intergov.repos.base.elasticmq.elasticmqrepo.boto3', autospec=True)
def test_operations(boto3):
    sqs_client = boto3.client.return_value
    sqs_client.get_queue_url.return_value = {'QueueUrl': QUEUE_URL}

    repo = ElasticMQRepo(CONNECTION_DATA)
    # testing post message
    message = _generate_msg_object()
    assert repo.post(message)
    sqs_client.send_message.assert_called_once_with(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(message.to_dict()),
        DelaySeconds=0
    )
    boto3.reset_mock()
    # testing post message exception
    sqs_client.send_message.side_effect = Exception()
    assert not repo.post(message)
    # testing get message
    sqs_client.receive_message.return_value = {
        "Messages": [
            {
                "ReceiptHandle": 'a',
                "Body": json.dumps(message.to_dict())
            }
        ]
    }
    queue_message_id, queue_message = repo.get()
    message_dict = message.to_dict()
    queue_message_dict = queue_message.to_dict()
    assert queue_message_id == 'a'
    for key, value in message_dict.items():
        assert queue_message_dict[key] == value
    sqs_client.receive_message.assert_called_once()
    args, kwargs = sqs_client.receive_message.call_args_list[0]
    assert kwargs['MaxNumberOfMessages'] == 1
    assert kwargs['VisibilityTimeout'] == 30
    boto3.reset_mock()
    # testing get empty responses
    sqs_client.receive_message.return_value = {
        "Messages": []
    }
    assert not repo.get()
    sqs_client.receive_message.return_value = {}
    assert not repo.get()
    # testing get invalid message payload
    sqs_client.receive_message.return_value = {
        "Messages": [
            {
                "ReceiptHandle": 'a',
                "Body": json.dumps({'Hello': 'world'})
            }
        ]
    }
    with pytest.raises(KeyError):
        repo.get()
    boto3.reset_mock()
    # testing post job
    sqs_client.send_message.side_effect = None
    job = {'Hello': 'job'}
    assert repo.post_job(job, delay_seconds=30)
    sqs_client.send_message.assert_called_once_with(
        QueueUrl=QUEUE_URL,
        DelaySeconds=30,
        MessageBody=json.dumps(job)
    )
    boto3.reset_mock()
    # testing post job exceptions
    # job is empty or None
    with pytest.raises(ValueError):
        repo.post_job({})
    # delay seconds is not int
    with pytest.raises(TypeError):
        repo.post_job(job, delay_seconds="30")
    boto3.reset_mock()
    # testing get_job
    sqs_client.receive_message.return_value = {
        "Messages": [
            {
                "ReceiptHandle": 'a',
                "Body": json.dumps(job)
            }
        ]
    }
    queue_job_id, queue_job = repo.get_job()
    args, kwargs = sqs_client.receive_message.call_args_list[0]
    assert kwargs['MaxNumberOfMessages'] == 1
    assert kwargs['VisibilityTimeout'] == 30
    assert queue_job_id == 'a'
    assert queue_job == job
    # testing get_job empty responses
    sqs_client.receive_message.return_value = {
        "Messages": []
    }
    assert not repo.get_job()
    sqs_client.receive_message.return_value = {}
    assert not repo.get_job()
    boto3.reset_mock()
    # testing delete operation
    assert repo.delete(1)
    sqs_client.delete_message.assert_called_once_with(
        QueueUrl=QUEUE_URL,
        ReceiptHandle=1
    )
    boto3.reset_mock()
    sqs_client.delete_message.side_effect = Exception()
    assert not repo.delete(2)
    sqs_client.delete_message.assert_called_once()


@mock.patch('intergov.repos.base.elasticmq.elasticmqrepo.IGL_ALLOW_UNSAFE_REPO_CLEAR', False)
@mock.patch('intergov.repos.base.elasticmq.elasticmqrepo.IGL_ALLOW_UNSAFE_REPO_IS_EMPTY', False)
@mock.patch('intergov.repos.base.elasticmq.elasticmqrepo.boto3', autospec=True)
def test_unsafe_operations_not_allowed(boto3):
    repo = ElasticMQRepo(CONNECTION_DATA)
    with pytest.raises(RuntimeError):
        repo._unsafe_clear_for_test()
    with pytest.raises(RuntimeError):
        repo._unsafe_is_empty_for_test()


@mock.patch('intergov.repos.base.elasticmq.elasticmqrepo.IGL_ALLOW_UNSAFE_REPO_CLEAR', True)
@mock.patch('intergov.repos.base.elasticmq.elasticmqrepo.IGL_ALLOW_UNSAFE_REPO_IS_EMPTY', True)
@mock.patch('intergov.repos.base.elasticmq.elasticmqrepo.boto3', autospec=True)
def test_unsafe_operations(boto3):
    sqs_client = boto3.client.return_value
    sqs_client.get_queue_url.return_value = {'QueueUrl': QUEUE_URL}
    repo = ElasticMQRepo(CONNECTION_DATA)
    repo._unsafe_clear_for_test()
    sqs_client.purge_queue.assert_called_once_with(
        QueueUrl=QUEUE_URL
    )
    payload = {'Hello': 'message'}
    sqs_client.receive_message.return_value = {
        "Messages": [
            {
                "ReceiptHandle": 'a',
                "Body": json.dumps(payload)
            }
        ]
    }
    assert not repo._unsafe_is_empty_for_test()
    sqs_client.receive_message.return_value = {
        "Messages": []
    }
    assert repo._unsafe_is_empty_for_test()
    sqs_client.receive_message.return_value = {}
    assert repo._unsafe_is_empty_for_test()

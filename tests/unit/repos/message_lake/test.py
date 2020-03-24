import json
from unittest import mock
import pytest
from intergov.repos.message_lake.minio.miniorepo import MessageLakeMinioRepo
from tests.unit.repos.base.minio.test import CONNECTION_DATA
from tests.unit.domain.wire_protocols.test_generic_message import _generate_msg_object


@mock.patch('intergov.repos.message_lake.minio.miniorepo.miniorepo.boto3')
def test_post(boto3):
    repo = MessageLakeMinioRepo(CONNECTION_DATA)
    boto3.client.assert_called_once()

    msg = _generate_msg_object(sender_ref='xxxx-xxxx-xxxx')
    assert repo.post(msg)

    s3_client = boto3.client.return_value
    assert s3_client.put_object.call_count == 2


@mock.patch('intergov.repos.message_lake.minio.miniorepo.miniorepo.boto3')
def test_update_metadata(boto3):
    repo = MessageLakeMinioRepo(CONNECTION_DATA)
    boto3.client.assert_called_once()
    msg = _generate_msg_object(sender_ref='xxxx-xxxx-xxxx', status='pending')
    metadata = {
        'status': 'received'
    }

    def get_object(**kwargs):
        key = kwargs['Key']
        body = mock.MagicMock()
        if key.endswith('metadata.json'):
            body.read.return_value = json.dumps(metadata).encode('utf-8')
            return {
                'Body': body
            }
        return None

    s3_client = boto3.client.return_value
    s3_client.get_object.side_effect = get_object

    assert repo.update_metadata(str(msg.sender), str(msg.sender_ref), {'status': 'received'})


@mock.patch('intergov.repos.message_lake.minio.miniorepo.ClientError', Exception)
@mock.patch('intergov.repos.message_lake.minio.miniorepo.miniorepo.boto3')
def test_get(boto3):
    repo = MessageLakeMinioRepo(CONNECTION_DATA)
    boto3.client.assert_called_once()
    msg = _generate_msg_object(sender_ref='xxxx-xxxx-xxxx', status='pending')
    msg_dict = msg.to_dict()
    metadata = {
        'status': 'received'
    }

    def get_object(**kwargs):
        key = kwargs['Key']
        body = mock.MagicMock()
        data = None
        if key.endswith('metadata.json'):
            data = metadata
        elif key.endswith('content.json'):
            data = msg_dict
        if data:
            body.read.return_value = json.dumps(data).encode('utf-8')
            return {
                'Body': body
            }

    s3_client = boto3.client.return_value
    s3_client.get_object.side_effect = get_object

    assert repo.get(str(msg.sender), str(msg.sender_ref))

    exception = Exception()
    exception.response = {
        'Error': {
            'Code': 'NoSuchKey'
        }
    }

    def raise_error(on_key):
        def get_object_content(key):
            if key.endswith(on_key):
                raise exception
            else:
                return json.dumps(msg_dict)
        return get_object_content

    s3_client = boto3.client.return_value
    repo.get_object_content = mock.Mock()
    repo.get_object_content.side_effect = raise_error('metadata.json')

    assert repo.get(str(msg.sender), str(msg.sender_ref))
    repo.get_object_content.side_effect = raise_error('content.json')
    assert not repo.get(str(msg.sender), str(msg.sender_ref))

    exception.response['Error']['Code'] = 'Random'
    for key in ['content.json', 'metadata.json']:
        repo.get_object_content.side_effect = raise_error(key)
        with pytest.raises(Exception):
            repo.get(str(msg.sender), str(msg.sender_ref))

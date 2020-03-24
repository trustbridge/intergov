from unittest import mock
from io import BytesIO
import pytest
from intergov.repos.base.minio.miniorepo import (
    MinioRepo,
    slash_chunk
)


URI_LEN_5 = '12345'
URI_LEN_10 = '1234567890'
URI_LEN_15 = URI_LEN_5 + URI_LEN_10
URI_LEN_25 = URI_LEN_5 + URI_LEN_10*2


CONNECTION_DATA = {
    'host': 'minio.host',
    'port': 1000,
    'access_key': 'access_key',
    'secret_key': 'secret_key',
    'bucket': 'bucket',
    'use_ssl': False
}

AWS_CONNECTION_DATA = {
    'aws_access_key_id': CONNECTION_DATA['access_key'],
    'aws_secret_access_key': CONNECTION_DATA['secret_key'],
    'endpoint_url': f"http://{CONNECTION_DATA['host']}:{CONNECTION_DATA['port']}/"
}

CONNECTION_DATA_SSL = {
    **CONNECTION_DATA,
    'use_ssl': True
}


AWS_CONNECTION_DATA_SSL = {
    'aws_access_key_id': CONNECTION_DATA_SSL['access_key'],
    'aws_secret_access_key': CONNECTION_DATA_SSL['secret_key'],
    'endpoint_url': f"https://{CONNECTION_DATA_SSL['host']}:{CONNECTION_DATA_SSL['port']}/"
}


def test_utils():
    assert slash_chunk(URI_LEN_5) == URI_LEN_5
    assert slash_chunk(URI_LEN_10) == URI_LEN_10
    assert slash_chunk(URI_LEN_15) == f'{URI_LEN_5}/{URI_LEN_10}'
    assert slash_chunk(URI_LEN_25) == f'{URI_LEN_5}/{URI_LEN_10*2}'


def test_aws_connection_args():
    assert MinioRepo._aws_connection_data(CONNECTION_DATA) == AWS_CONNECTION_DATA
    assert MinioRepo._aws_connection_data(CONNECTION_DATA_SSL) == AWS_CONNECTION_DATA_SSL


@mock.patch('intergov.repos.base.minio.miniorepo.ClientError', Exception)
@mock.patch('intergov.repos.base.minio.miniorepo.boto3', autospec=True)
def test_initialization(boto3):
    # test missing connection data keys errors
    for key in CONNECTION_DATA.keys():
        missing_key_connection_data = {**CONNECTION_DATA}
        del missing_key_connection_data[key]
        with pytest.raises(KeyError) as einfo:
            MinioRepo(missing_key_connection_data)
        assert str(einfo.value) == str(KeyError(key))

    # test initialization
    s3_client = boto3.client.return_value
    # initialization without ssl
    MinioRepo(CONNECTION_DATA)
    boto3.client.assert_called_once_with('s3', **AWS_CONNECTION_DATA)
    s3_client.head_bucket.assert_called_once_with(Bucket=CONNECTION_DATA['bucket'])
    s3_client.create_bucket.assert_not_called()
    boto3.reset_mock()

    # initialization with ssl
    MinioRepo(CONNECTION_DATA_SSL)
    boto3.client.assert_called_once_with('s3', **AWS_CONNECTION_DATA_SSL)
    s3_client.head_bucket.assert_called_once_with(Bucket=CONNECTION_DATA['bucket'])
    s3_client.create_bucket.assert_not_called()
    boto3.reset_mock()

    # test initialization with default bucket
    missing_bucket_connection_data = {**CONNECTION_DATA}
    del missing_bucket_connection_data['bucket']

    class DefaultBucketRepo(MinioRepo):
        DEFAULT_BUCKET = 'default_bucket'
    DefaultBucketRepo(missing_bucket_connection_data)

    boto3.client.assert_called_once_with('s3', **AWS_CONNECTION_DATA)
    s3_client.head_bucket.assert_called_once_with(Bucket=DefaultBucketRepo.DEFAULT_BUCKET)
    s3_client.create_bucket.assert_not_called()
    boto3.reset_mock()

    # testing bucket not found
    s3_client.head_bucket.side_effect = Exception()
    MinioRepo(CONNECTION_DATA)
    boto3.client.assert_called_once_with('s3', **AWS_CONNECTION_DATA)
    s3_client.head_bucket.assert_called_once_with(Bucket=CONNECTION_DATA['bucket'])
    s3_client.create_bucket.assert_called_once_with(Bucket=CONNECTION_DATA['bucket'])
    boto3.reset_mock()


@mock.patch('intergov.repos.base.minio.miniorepo.boto3', autospec=True)
def test_operations(boto3):

    CONTENT = "dummy_content"
    CONTENT_BYTES = CONTENT.encode('utf-8')

    class DummyFileLikeObj():
        def read(self):
            return CONTENT

    s3_client = boto3.client.return_value
    # testing successful get
    repo = MinioRepo(CONNECTION_DATA)
    s3_client.get_object.return_value = {'Body': DummyFileLikeObj()}
    assert CONTENT == repo.get_object_content('path_to_object')
    boto3.reset_mock()

    # testing successful put
    repo.put_message_related_object('AU', URI_LEN_25, '/metadata.json', CONTENT)
    s3_client.put_object.assert_called_once()

    args, kwargs = s3_client.put_object.call_args_list[0]
    assert kwargs['Bucket'] == CONNECTION_DATA['bucket']
    assert kwargs['ContentLength'] == len(CONTENT_BYTES)
    assert kwargs['Key'] == f'AU/{URI_LEN_5}/{URI_LEN_10*2}/metadata.json'
    assert isinstance(kwargs.get('Body'), BytesIO)
    assert kwargs['Body'].read() == CONTENT_BYTES

    boto3.reset_mock()

    # testing invalid sender
    with pytest.raises(ValueError):
        repo.put_message_related_object('Au', URI_LEN_25, '/metadata.json', CONTENT)
    with pytest.raises(ValueError):
        repo.put_message_related_object('AUU', URI_LEN_25, '/metadata.json', CONTENT)

    # testing put object with clear path. Path will be chunked in the process
    repo.put_object(clean_path=URI_LEN_25, content_body=CONTENT)
    s3_client.put_object.assert_called_once()

    args, kwargs = s3_client.put_object.call_args_list[0]
    assert kwargs['Bucket'] == CONNECTION_DATA['bucket']
    assert kwargs['ContentLength'] == len(CONTENT_BYTES)
    assert kwargs['Key'] == f'{URI_LEN_5}/{URI_LEN_10*2}'
    assert isinstance(kwargs.get('Body'), BytesIO)
    assert kwargs['Body'].read() == CONTENT_BYTES

    boto3.reset_mock()

    # testing put object with chunked path. Path should not be chunked in the process
    repo.put_object(chunked_path=URI_LEN_25, content_body=CONTENT)
    s3_client.put_object.assert_called_once()

    args, kwargs = s3_client.put_object.call_args_list[0]
    assert kwargs['Bucket'] == CONNECTION_DATA['bucket']
    assert kwargs['ContentLength'] == len(CONTENT_BYTES)
    assert kwargs['Key'] == URI_LEN_25
    assert isinstance(kwargs.get('Body'), BytesIO)
    assert kwargs['Body'].read() == CONTENT_BYTES

    boto3.reset_mock()

    # testing both chunked and clear path error
    with pytest.raises(TypeError):
        repo.put_object(chunked_path=URI_LEN_25, clean_path=URI_LEN_25, content_body=CONTENT)
    with pytest.raises(TypeError):
        repo.put_object(content_body=CONTENT)


@mock.patch('intergov.repos.base.minio.miniorepo.IGL_ALLOW_UNSAFE_REPO_CLEAR', False)
@mock.patch('intergov.repos.base.minio.miniorepo.IGL_ALLOW_UNSAFE_REPO_IS_EMPTY', False)
@mock.patch('intergov.repos.base.minio.miniorepo.boto3', autospec=True)
def test_unsafe_operations_not_allowed(boto3):
    repo = MinioRepo(CONNECTION_DATA)
    with pytest.raises(RuntimeError):
        repo._unsafe_clear_for_test()
    with pytest.raises(RuntimeError):
        repo._unsafe_is_empty_for_test()


@mock.patch('intergov.repos.base.minio.miniorepo.IGL_ALLOW_UNSAFE_REPO_CLEAR', True)
@mock.patch('intergov.repos.base.minio.miniorepo.IGL_ALLOW_UNSAFE_REPO_IS_EMPTY', True)
@mock.patch('intergov.repos.base.minio.miniorepo.boto3', autospec=True)
def test_unsafe_operations(boto3):
    s3_client = boto3.client.return_value
    repo = MinioRepo(CONNECTION_DATA)

    # testing unsafe clear method
    s3_client.list_objects.return_value = {
        'Contents': [
            {
                'Key': 'a'
            },
            {
                'Key': 'b'
            }
        ],
        'IsTruncated': False
    }
    # deleted 2 objects
    assert repo._unsafe_clear_for_test() == 2
    s3_client.list_objects.assert_called_once_with(Bucket=CONNECTION_DATA['bucket'])
    # deleted only objects from the response
    assert s3_client.delete_object.call_count == 2
    assert s3_client.delete_object.call_args_list == [
        mock.call(Bucket=CONNECTION_DATA['bucket'], Key='a'),
        mock.call(Bucket=CONNECTION_DATA['bucket'], Key='b')
    ]
    boto3.reset_mock()
    # testing unsafe is empty
    assert not repo._unsafe_is_empty_for_test()
    s3_client.list_objects.assert_called_once_with(Bucket=CONNECTION_DATA['bucket'])
    boto3.reset_mock()

    s3_client.list_objects.return_value['Contents'] = []
    assert repo._unsafe_is_empty_for_test()
    s3_client.list_objects.assert_called_once_with(Bucket=CONNECTION_DATA['bucket'])
    boto3.reset_mock()

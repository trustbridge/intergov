import hashlib
import json
from unittest import mock
from datetime import datetime, timedelta
import pytest
from intergov.repos.subscriptions import SubscriptionsRepo
from intergov.repos.subscriptions.minio.miniorepo import (
    current_datetime,
    expiration_datetime,
    url_to_filename
)
from tests.unit.repos.base.minio.test import CONNECTION_DATA

UTC_NOW = datetime.utcnow()


@mock.patch('intergov.repos.subscriptions.minio.miniorepo.datetime', autospec=True)
def test_utils(datetime_mock):
    datetime_mock.utcnow.return_value = UTC_NOW
    assert current_datetime() == UTC_NOW
    assert expiration_datetime(3600) == current_datetime() + timedelta(seconds=3600)
    assert url_to_filename('a') == hashlib.md5('a'.encode('utf-8')).hexdigest()


@mock.patch('intergov.repos.subscriptions.minio.miniorepo.datetime', autospec=True)
@mock.patch('intergov.repos.subscriptions.minio.miniorepo.miniorepo.boto3')
def test_repo_utils(boto3, datetime_mock):
    datetime_mock.utcnow = UTC_NOW
    repo = SubscriptionsRepo(CONNECTION_DATA)
    boto3.client.assert_called_once()
    # test pattern to key. Pattern == predicate
    # error should be not empty
    with pytest.raises(ValueError):
        repo._pattern_to_key('')
    # # error should not contain slashes UPD: it's fine now
    # with pytest.raises(ValueError):
    #     repo._pattern_to_key('aa/bb')
    assert repo._pattern_to_key('aaaa.bbbb.cccc') == "AAAA/BBBB/CCCC/"
    assert repo._pattern_to_key('aaaa.bbbb.cccc.*') == repo._pattern_to_key('aaaa.bbbb.cccc')
    assert repo._pattern_to_key('aaaa.bbbb.cccc.') == repo._pattern_to_key('aaaa.bbbb.cccc')

    assert (
        repo._predicate_url_to_key('aaaa.bbbb.cccc', 'a')
        == repo._pattern_to_key('aaaa.bbbb.cccc')+url_to_filename('a')
    )

    # test pattern to layers
    assert repo._pattern_to_layers('aaaa.bbbb.cccc') == [
        'AAAA/',
        'AAAA/BBBB/',
        'AAAA/BBBB/CCCC/'
    ]

    assert repo._pattern_to_layers('aaaa.bbbb.cccc.*') == [
        'AAAA/',
        'AAAA/BBBB/',
        'AAAA/BBBB/CCCC/'
    ]

    callback = 'http://callback.com/1'
    expiration = UTC_NOW

    valid_body = {
        'e': expiration.isoformat(),
        'c': callback
    }

    valid_decoded_body = {
        'c': callback,
        'e': expiration
    }

    assert json.loads(repo._encode_obj(callback, expiration).decode('utf-8')) == valid_body

    expired_encoded_body = repo._encode_obj(callback, expiration - timedelta(days=10))

    body = mock.MagicMock()
    body.read.return_value = repo._encode_obj(callback, expiration)

    obj = {
        'Body': body
    }
    # correct subscription payload
    assert repo._decode_obj(obj) == valid_decoded_body
    # testing unicode error
    body.read.return_value = "Hello world".encode('utf-16')
    assert repo._decode_obj(obj) is None
    # testing json decode error
    body.read.return_value = "Hello world".encode('utf-8')
    assert repo._decode_obj(obj) is None
    # testing key error
    body.read.return_value = json.dumps({'c': callback}).encode('utf-8')
    assert repo._decode_obj(obj) is None
    # testing invalid datetime format
    body.read.return_value = json.dumps({'c': callback, 'e': 'asfasfasfs'}).encode('utf-8')
    assert repo._decode_obj(obj) is None
    # testing expired subscription
    body.read.return_value = expired_encoded_body
    assert repo._decode_obj(obj, now=UTC_NOW) is None
    # testing delete if name provided
    body.read.return_value = expired_encoded_body
    assert repo._decode_obj(obj, now=UTC_NOW, name="test") is None
    repo.client.delete_objects.assert_called_once()
    boto3.reset_mock()
    # testing put to invalid list if name and list provided
    body.read.return_value = expired_encoded_body
    invalids_list = []
    assert repo._decode_obj(obj, now=UTC_NOW, name="test", invalids_list=invalids_list) is None
    repo.client.delete_objects.assert_not_called()
    assert len(invalids_list) == 1


@mock.patch('intergov.repos.subscriptions.minio.miniorepo.ClientError', Exception)
@mock.patch('intergov.repos.subscriptions.minio.miniorepo.miniorepo.boto3')
def test_post(boto3):
    repo = SubscriptionsRepo(CONNECTION_DATA)
    boto3.client.assert_called_once()

    callback = 'http://callback.com/callme/'
    predicate = 'test.predicate.*'
    expiration = 3600

    assert repo.post(callback, predicate, expiration)


@mock.patch('intergov.repos.subscriptions.minio.miniorepo.ClientError', Exception)
@mock.patch('intergov.repos.subscriptions.minio.miniorepo.datetime', autospec=True)
@mock.patch('intergov.repos.subscriptions.minio.miniorepo.miniorepo.boto3')
def test_get(boto3, datetime_mock):
    repo = SubscriptionsRepo(CONNECTION_DATA)
    boto3.client.assert_called_once()
    datetime_mock.utcnow.return_value = UTC_NOW

    callback = 'http://callback.com/callme/'
    predicate = 'test.predicate.*'
    expiration = UTC_NOW

    body = mock.MagicMock()
    body.read.return_value = repo._encode_obj(callback, expiration)
    no_obj_error = Exception()
    random_error = RuntimeError()
    no_obj_error.response = {
        'Error': {
            'Code': 'NoSuchKey'
        }
    }
    random_error.response = {
        'Error': {
            'Code': 'RandomError'
        }
    }

    repo.client.get_object.side_effect = [
        {
            'Body': body
        },
        no_obj_error,
        random_error
    ]

    # no error
    assert repo.get(callback, predicate)
    # no such key error
    assert repo.get(callback, predicate) is None
    # random error
    with pytest.raises(RuntimeError):
        repo.get(callback, predicate)


@mock.patch('intergov.repos.subscriptions.minio.miniorepo.ClientError', Exception)
@mock.patch('intergov.repos.subscriptions.minio.miniorepo.datetime', autospec=True)
@mock.patch('intergov.repos.subscriptions.minio.miniorepo.miniorepo.boto3')
def test_delete(boto3, datetime_mock):
    repo = SubscriptionsRepo(CONNECTION_DATA)
    boto3.client.assert_called_once()
    datetime_mock.utcnow.return_value = UTC_NOW

    callback = 'http://callback.com/callme/'
    predicate = 'test.predicate.*'
    # delete one subscription
    no_obj_error = Exception()
    random_error = RuntimeError()
    no_obj_error.response = {
        'Error': {
            'Code': 'NoSuchKey'
        }
    }
    random_error.response = {
        'Error': {
            'Code': 'RandomError'
        }
    }

    repo.client.delete_objects.side_effect = [
        no_obj_error,
        random_error
    ]
    # no such key
    assert repo.delete(callback, predicate) == 0
    # random error
    with pytest.raises(RuntimeError):
        repo.delete(callback, predicate)
    repo.client.delete_objects.side_effect = None
    # sucessful deletion
    assert repo.delete(callback, predicate) == 1
    repo.client.list_objects.return_value = {
        'Contents': [
            {
                'Key': 'a'
            },
            {
                'Key': 'b'
            }
        ]
    }
    body = mock.MagicMock()
    body.read.return_value = repo._encode_obj(callback, UTC_NOW)
    repo.client.get_object.return_value = {
        'Body': body
    }
    # delete many
    assert repo.delete(None, predicate) == 2
    # expired objects not marked as deleted
    datetime_mock.utcnow.return_value = UTC_NOW + timedelta(days=1)
    assert repo.delete(None, predicate) == 0


@mock.patch('intergov.repos.subscriptions.minio.miniorepo.ClientError', Exception)
@mock.patch('intergov.repos.subscriptions.minio.miniorepo.datetime', autospec=True)
@mock.patch('intergov.repos.subscriptions.minio.miniorepo.miniorepo.boto3')
def test_search(boto3, datetime_mock):
    repo = SubscriptionsRepo(CONNECTION_DATA)
    boto3.client.assert_called_once()
    datetime_mock.utcnow.return_value = UTC_NOW

    callback = 'http://callback.com/callme/'
    predicate = 'test.predicate.*'

    repo.client.list_objects.return_value = {
        'Contents': [
            {
                'Key': 'a'
            },
            {
                'Key': 'b'
            }
        ]
    }
    body = mock.MagicMock()

    # broad search returns only unique callbacks
    def read():
        callback_index = 0
        while True:
            callback_index += 1
            yield repo._encode_obj(callback+str(callback_index), UTC_NOW)

    body.read.side_effect = read()
    repo.client.get_object.return_value = {
        'Body': body
    }
    # search using callback and predicate == get
    assert repo.search(predicate, url=callback)
    no_obj_error = Exception()
    no_obj_error.response = {
        'Error': {
            'Code': 'NoSuchKey'
        }
    }
    # not found
    repo.client.get_object.side_effect = no_obj_error
    assert repo.search(predicate, url=callback) is None
    repo.client.get_object.side_effect = None
    # broad search
    assert len(repo.search(predicate)) == 2
    # don't return expired callbacks
    datetime_mock.utcnow.return_value = UTC_NOW + timedelta(days=1)
    assert len(repo.search(predicate)) == 0
    # layered search
    datetime_mock.utcnow.return_value = UTC_NOW
    repo.client.list_objects.side_effect = [
        {
            'Contents': [
                {
                    'Key': 'a'
                },
                {
                    'Key': 'b'
                },
                {
                    # recursive will not be included
                    'Key': repo._pattern_to_key(predicate)+'b/c/d'
                }
            ]
        },
        {
            'Contents': [
                {
                    'Key': 'c'
                },
                {
                    'Key': 'd'
                }
            ]
        }
    ]
    assert len(repo.search(predicate, layered=True)) == 4
    # layered recursive search is not allowed
    with pytest.raises(ValueError):
        repo.search(predicate, layered=True, recursive=True)

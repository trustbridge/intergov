import os
from unittest import mock
import pytest
from intergov.conf import env_s3_config
from intergov.repos.base.minio.miniorepo import MinioRepo
from intergov.repos.base.minio.minio_objects import Message


def test_minio_objects():
    message = Message(
        'sender',
        'receiver',
        'subject',
        'obj',
        'predicate',
        'status'
    )
    assert message.sender == 'sender'
    assert message.receiver == 'receiver'
    assert message.subject == 'subject'
    assert message.obj == 'obj'
    assert message.predicate == 'predicate'
    assert message.status == 'status'

    message = Message(
        'sender',
        'receiver',
        'subject',
        'obj',
        'predicate'
    )
    assert message.sender == 'sender'
    assert message.receiver == 'receiver'
    assert message.subject == 'subject'
    assert message.obj == 'obj'
    assert message.predicate == 'predicate'
    assert message.status is None


TEST_CONFIG = env_s3_config('TEST')


@mock.patch('intergov.repos.base.minio.miniorepo.IGL_ALLOW_UNSAFE_REPO_CLEAR', False)
@mock.patch('intergov.repos.base.minio.miniorepo.IGL_ALLOW_UNSAFE_REPO_IS_EMPTY', False)
def test_unsafe_methods():
    repo = MinioRepo(TEST_CONFIG)
    with pytest.raises(RuntimeError):
        repo._unsafe_clear_for_test()
    with pytest.raises(RuntimeError):
        repo._unsafe_is_empty_for_test()


@mock.patch('intergov.repos.base.minio.miniorepo.MinioRepo.DEFAULT_BUCKET', TEST_CONFIG['bucket'])
def test_default_bucket():
    conf = {**TEST_CONFIG, 'bucket': None}
    repo = MinioRepo(conf)
    assert repo.bucket == TEST_CONFIG['bucket']

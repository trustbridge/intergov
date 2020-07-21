from intergov.conf import env_s3_config
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

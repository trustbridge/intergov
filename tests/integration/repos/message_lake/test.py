import json
from intergov.conf import env_s3_config
from intergov.domain.wire_protocols.generic_discrete import Message
from intergov.repos.message_lake import MessageLakeRepo
from tests.unit.domain.wire_protocols.test_generic_message import (
    _generate_msg_object
)


CONF = env_s3_config('TEST')


def test():
    repo = MessageLakeRepo(CONF)
    repo._unsafe_method__clear()
    assert repo.is_empty()

    message = _generate_msg_object(
        sender_ref='xxx-xxx-xxx', status=None,
        channel_id=None, channel_txn_id=None,
    )
    assert repo.post(message)

    sender = str(message.sender)
    sender_ref = str(message.sender_ref)
    message_from_repo = repo.get(sender, sender_ref)
    assert message_from_repo
    assert isinstance(message_from_repo, Message)
    assert message_from_repo.to_dict() == message.to_dict()

    message.status = 'rejected'
    assert repo.update_metadata(sender, sender_ref, {'status':  message.status})
    message_from_repo = repo.get(sender, sender_ref)
    assert message_from_repo
    assert message_from_repo == message

    assert not repo.get('AU', 'aaaaa-bbbbb-ccccc')
    repo._unsafe_method__clear()
    assert repo.is_empty()

    repo.put_message_related_object(
        sender=sender,
        sender_ref=sender_ref,
        rel_path='/content.json',
        content_body=json.dumps(message.to_dict())
    )

    message_from_repo = repo.get(sender, sender_ref)
    assert message == message_from_repo

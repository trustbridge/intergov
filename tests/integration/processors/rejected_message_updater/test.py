from intergov.conf import env_s3_config, env_queue_config
from intergov.repos.message_lake import MessageLakeRepo
from intergov.repos.rejected_message import RejectedMessagesRepo
from intergov.processors.rejected_status_updater import RejectedStatusUpdater
from intergov.domain.wire_protocols.generic_discrete import (
    SENDER_KEY,
    SENDER_REF_KEY,
    Message
)
from tests.unit.domain.wire_protocols.test_generic_message import (
    _generate_msg_dict
)


MESSAGES_DATA = [
    ('AU', 'aaaa'),
    ('US', 'bbbb'),
    ('DE', 'cccc'),
    ('FR', 'dddd'),
    ('GB', 'eeee'),
    ('UA', 'ffff'),
]

# required to not share repos with running workers
MESSAGE_LAKE_REPO_CONF = env_s3_config('TEST')
REJECTED_MESSAGES_REPO_CONF = env_queue_config('TEST')


def test(docker_setup):

    message_lake_repo = MessageLakeRepo(MESSAGE_LAKE_REPO_CONF)
    rejected_message_repo = RejectedMessagesRepo(REJECTED_MESSAGES_REPO_CONF)

    # ensuring that repos are empty
    message_lake_repo._unsafe_clear_for_test()
    rejected_message_repo._unsafe_clear_for_test()

    updater = RejectedStatusUpdater(
        rejected_message_repo_conf=REJECTED_MESSAGES_REPO_CONF,
        message_lake_repo_conf=MESSAGE_LAKE_REPO_CONF
    )

    # checking that iter returns updater
    assert updater is iter(updater)

    # test no rejected messages in the queue
    assert not next(updater)

    # testing single message in the queue
    sender, sender_ref = MESSAGES_DATA[0]
    message = Message.from_dict(
        _generate_msg_dict(
            **{
                SENDER_KEY: sender,
                SENDER_REF_KEY: sender_ref
            }
        )
    )
    rejected_message_repo.post(message)
    message_lake_repo.post(message)

    assert next(updater)
    assert not next(updater)

    # testing several messages in queue
    for i in range(2):
        for sender, sender_ref in MESSAGES_DATA:
            message = Message.from_dict(_generate_msg_dict(
                **{
                    SENDER_KEY: sender,
                    SENDER_REF_KEY: sender_ref
                }
            ))
            rejected_message_repo.post(message)
            message_lake_repo.post(message)
        for i in range(len(MESSAGES_DATA)):
            assert next(updater)
        assert not next(updater)

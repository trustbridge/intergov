from intergov.conf import env_s3_config, env_queue_config, env_postgres_config, env
from intergov.processors.message_processor import InboundMessageProcessor
from intergov.repos.api_outbox import ApiOutboxRepo
from intergov.repos.bc_inbox.elasticmq.elasticmqrepo import BCInboxRepo
from intergov.repos.message_lake import MessageLakeRepo
from intergov.repos.notifications import NotificationsRepo
from intergov.repos.object_acl import ObjectACLRepo
from intergov.repos.object_retrieval import ObjectRetrievalRepo
from tests.unit.domain.wire_protocols.test_generic_message import (
    _generate_msg_object
)

MESSAGE_LAKE_REPO_CONF = env_s3_config('TEST_1')
OBJECT_ACL_REPO_CONF = env_s3_config('TEST_2')

BC_INBOX_REPO_CONF = env_queue_config('TEST_1')
OBJECT_RETRIEVAL_REPO_CONF = env_queue_config('TEST_2')
NOTIFICATIONS_REPO_CONF = env_queue_config('TEST_3')

BLOCKCHAIN_OUTBOX_REPO_CONF = env_postgres_config('TEST')

OUR_JRD = env("IGL_COUNTRY", default="AU")


def test():
    # creating testing versions of all required repos
    message_lake_repo = MessageLakeRepo(MESSAGE_LAKE_REPO_CONF)
    object_acl_repo = ObjectACLRepo(OBJECT_ACL_REPO_CONF)

    bc_inbox_repo = BCInboxRepo(BC_INBOX_REPO_CONF)
    object_retrieval_repo = ObjectRetrievalRepo(OBJECT_RETRIEVAL_REPO_CONF)
    notifications_repo = NotificationsRepo(NOTIFICATIONS_REPO_CONF)

    blockchain_outbox_repo = ApiOutboxRepo(BLOCKCHAIN_OUTBOX_REPO_CONF)

    def clear():
        # clearing repos
        message_lake_repo._unsafe_method__clear()
        object_acl_repo._unsafe_method__clear()

        bc_inbox_repo._unsafe_method__clear()
        object_retrieval_repo._unsafe_method__clear()
        notifications_repo._unsafe_method__clear()

        blockchain_outbox_repo._unsafe_method__clear()

        # test repos are empty
        assert message_lake_repo.is_empty()
        assert object_acl_repo.is_empty()

        assert bc_inbox_repo.is_empty()
        assert object_retrieval_repo.is_empty()
        assert notifications_repo.is_empty()

        assert blockchain_outbox_repo.is_empty()

    clear()

    processor = InboundMessageProcessor(
        bc_inbox_repo_conf=BC_INBOX_REPO_CONF,
        message_lake_repo_conf=MESSAGE_LAKE_REPO_CONF,
        object_acl_repo_conf=OBJECT_ACL_REPO_CONF,
        object_retrieval_repo_conf=OBJECT_RETRIEVAL_REPO_CONF,
        notifications_repo_conf=NOTIFICATIONS_REPO_CONF,
        blockchain_outbox_repo_conf=BLOCKCHAIN_OUTBOX_REPO_CONF
    )

    # test iter processor returns processor
    assert iter(processor) is processor
    # test processor has no jobs
    assert next(processor) is None

    sender_ref = "AU:xxxx-xxxx-xxxx"
    status = 'received'
    message = _generate_msg_object(sender_ref=sender_ref, status=status)
    message.sender = "CN"

    assert bc_inbox_repo.post(message)

    # testing normal execution received message with sender ref
    assert next(processor) is True
    assert next(processor) is None
    # testing that message is deleted
    assert bc_inbox_repo.is_empty()
    # testing message posted to related repos
    assert not message_lake_repo.is_empty()
    assert not object_acl_repo.is_empty()
    # we can't say it's empty because worker gets values from there
    # assert not object_retrieval_repo.is_empty()
    # received status should not be posted to blockchain
    assert blockchain_outbox_repo.is_empty()

    clear()

    sender_ref = "AU:xxxx-xxxx-xxxx"
    # this one should go to blockchain outbox
    status = 'pending'
    message = _generate_msg_object(sender_ref=sender_ref, status=status)
    message.sender = OUR_JRD
    message.receiver = 'CN'

    assert bc_inbox_repo.post(message)

    # testing normal execution received message with sender ref
    assert next(processor) is True
    assert next(processor) is None
    # testing that message is deleted
    assert bc_inbox_repo.is_empty()
    # testing message posted to related repos
    assert not message_lake_repo.is_empty()
    assert not object_acl_repo.is_empty()

    clear()

    # message without sender ref should fail
    message = _generate_msg_object()
    assert bc_inbox_repo.post(message)

    assert next(processor) is False
    assert next(processor) is None
    # This part is a tricky thing.
    # Therefore I will not dig deep. I just check basic execution.
    # Without transaction some repos will fail, some will not.
    # Therefore this part should be covered by an unit test.
    # Integration test will look very very strange if I'll try to
    # test fail behavior in it.

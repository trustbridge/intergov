from intergov.conf import env_queue_config, env_postgres_config
from intergov.repos.api_outbox import ApiOutboxRepo
from intergov.domain.wire_protocols.generic_discrete import (
    Message
)
from intergov.repos.rejected_message import RejectedMessagesRepo
from intergov.processors.loopback_bch_worker import LoopbackBlockchainWorker
from tests.unit.domain.wire_protocols.test_generic_message import (
    _generate_msg_dict
)

TEST_API_OUTBOX_REPO_CONF = env_postgres_config('TEST')
TEST_REJECTED_MESSAGES_REPO_CONF = env_queue_config('TEST')


def _generate_msg(**kwargs):
    return Message.from_dict(_generate_msg_dict(**kwargs))


def _generate_sender_ref(base):
    return "-".join([(f"{base}"*3)]*3)


def test():

    api_outbox_repo = ApiOutboxRepo(TEST_API_OUTBOX_REPO_CONF)
    rejected_messages_repo = RejectedMessagesRepo(TEST_REJECTED_MESSAGES_REPO_CONF)
    api_outbox_repo._unsafe_clear_for_test()
    rejected_messages_repo._unsafe_clear_for_test()

    # check that repos are really empty
    assert not api_outbox_repo.get_next_pending_message()
    assert not rejected_messages_repo.get()

    worker = LoopbackBlockchainWorker(
        blockchain_outbox_repo_conf=TEST_API_OUTBOX_REPO_CONF,
        rejected_messages_repo_conf=TEST_REJECTED_MESSAGES_REPO_CONF
    )

    # testing that iter returns worker
    assert worker is iter(worker)

    worker.REJECT_EACH = 3

    # check that worker has nothing to do
    assert not next(worker)

    # posting messages/filling outbox
    msg_ids = []
    for i in range(worker.REJECT_EACH*3):
        message = _generate_msg(sender_ref=_generate_sender_ref(i), status='pending')
        msg_id = api_outbox_repo.post(message)
        assert msg_id
        msg_ids.append(msg_id)

    # checking that worker received all messages + rejected some of them
    for i in range(worker.REJECT_EACH*3):
        assert next(worker)
        # testing that messages rejected and posted into the queue
        if i + 1 % worker.REJECT_EACH == 0:
            rejected_message = rejected_messages_repo.get()
            assert rejected_message
            rejected_message_queue_id, rejected_message_obj = rejected_message
            assert rejected_messages_repo.delete(rejected_message_queue_id)
    # checking that worker completed all tasks
    assert not next(worker)

    # we don't know the order of messages therefore we just checking number of accepted/rejected
    accepted = 0
    rejected = 0
    for msg_id in msg_ids:
        api_outbox_message = api_outbox_repo.get(msg_id)
        assert api_outbox_message
        if api_outbox_message.status == 'accepted':
            accepted += 1
        elif api_outbox_message.status == 'rejected':
            rejected += 1

    expect_rejected = len(msg_ids)//worker.REJECT_EACH
    expect_accepted = len(msg_ids) - expect_rejected
    assert accepted == expect_accepted
    assert rejected == expect_rejected

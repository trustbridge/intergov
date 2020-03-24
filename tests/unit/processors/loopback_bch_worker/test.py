from unittest import mock
from http import HTTPStatus
from intergov.processors.loopback_bch_worker import LoopbackBlockchainWorker

API_OUTBOX_CONF = {
    'test': 'api-outbox'
}

REJECTED_MESSAGES_CONF = {
    'test': 'rejected-messages'
}


@mock.patch('intergov.processors.loopback_bch_worker.ApiOutboxRepo')
@mock.patch('intergov.processors.loopback_bch_worker.RejectedMessagesRepo')
@mock.patch('intergov.processors.loopback_bch_worker.requests')
def test(requests, RejectedMessagesRepo, ApiOutboxRepo):
    worker = LoopbackBlockchainWorker(
        rejected_messages_repo_conf=REJECTED_MESSAGES_CONF,
        blockchain_outbox_repo_conf=API_OUTBOX_CONF
    )
    RejectedMessagesRepo.assert_called_once()
    ApiOutboxRepo.assert_called_once()

    rejected_messages_repo = RejectedMessagesRepo.return_value
    blockchain_outbox_repo = ApiOutboxRepo.return_value

    args, kwargs = RejectedMessagesRepo.call_args_list[0]
    assert kwargs.items() <= REJECTED_MESSAGES_CONF.items()
    args, kwargs = ApiOutboxRepo.call_args_list[0]
    assert kwargs.items() <= REJECTED_MESSAGES_CONF.items()

    message = mock.MagicMock()
    message.id = 1

    post = requests.post
    patch = requests.patch

    post_response = mock.MagicMock()
    post_response.status_code = HTTPStatus.CREATED
    post.return_value = post_response

    patch_response = mock.MagicMock()
    patch_response.status_code = HTTPStatus.OK
    patch.return_value = patch_response

    worker.REJECT_EACH = 3
    assert iter(worker) is worker
    blockchain_outbox_repo.get_next_pending_message.return_value = None
    assert next(worker) is None
    blockchain_outbox_repo.get_next_pending_message.return_value = message
    for i in range(worker.REJECT_EACH-1):
        assert next(worker) is True
        post.assert_called_once()
        patch.assert_called_once()
        requests.reset_mock()
    assert next(worker) is True
    post.assert_not_called()
    patch.assert_not_called()
    rejected_messages_repo.post.assert_called_once()
    requests.reset_mock()

    patch_response.status_code = HTTPStatus.NOT_FOUND
    assert next(worker) is None
    patch_response.status_code = HTTPStatus.OK
    post_response.status_code = HTTPStatus.CONFLICT
    assert next(worker) is None

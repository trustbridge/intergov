from libtrustbridge.utils.conf import env_queue_config
from libtrustbridge.websub.processors import Processor
from libtrustbridge.websub.repos import DeliveryOutboxRepo

from intergov.use_cases import DeliverCallbackUseCase
from tests.unit.domain.wire_protocols.test_generic_message import (
    _generate_msg_dict
)

DELIVERY_OUTBOX_REPO_CONF = env_queue_config('TEST')

POST_SUCCESS_URL = "http://test-server-dummy-test-helper:5000/response/200/success"
POST_ERROR_URL = "http://test-server-dummy-test-helper:5000/response/500/internal-error"


def _generate_job(url, payload=None):
    if not payload:
        payload = _generate_msg_dict()
    return {
        's': url,
        'payload': payload
    }


def _test_retries(processor, max_attempts):
    retries = 0
    attempts = 0
    while retries < DeliverCallbackUseCase.MAX_RETRIES and attempts < max_attempts:
        if next(processor) is False:
            retries += 1
        attempts += 1
    assert retries == DeliverCallbackUseCase.MAX_RETRIES


def test_callback_delivery():
    delivery_outbox_repo = DeliveryOutboxRepo(DELIVERY_OUTBOX_REPO_CONF)
    use_case = DeliverCallbackUseCase(delivery_outbox_repo)
    # clearing test queue
    delivery_outbox_repo._unsafe_method__clear()
    assert not delivery_outbox_repo.get()
    processor = Processor(use_case=use_case)
    # testing that iter returns processor
    assert processor is iter(processor)
    # testing no jobs in the queue
    assert next(processor) is None
    # testing successful delivery
    job = _generate_job(POST_SUCCESS_URL)
    delivery_outbox_repo.post_job(job)
    assert next(processor) is True
    assert next(processor) is None
    # testing failed delivery
    job = _generate_job(POST_ERROR_URL)
    delivery_outbox_repo.post_job(job)
    # false means failed to deliver
    assert next(processor) is False
    _test_retries(processor, 10)
    assert next(processor) is None
    # testing correct rescheduling order
    delivery_outbox_repo.post_job(_generate_job(POST_SUCCESS_URL))
    delivery_outbox_repo.post_job(_generate_job(POST_ERROR_URL))
    delivery_outbox_repo.post_job(_generate_job(POST_SUCCESS_URL))
    assert next(processor) is True
    assert next(processor) is False
    assert next(processor) is True
    _test_retries(processor, 10)
    assert next(processor) is None

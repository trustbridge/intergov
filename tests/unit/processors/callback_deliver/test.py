from unittest import mock
from intergov.processors.callback_deliver import CallbacksDeliveryProcessor
from tests.unit.repos.base.elasticmq.test import CONNECTION_DATA


@mock.patch('intergov.processors.callback_deliver.DeliveryOutboxRepo', autospec=True)
@mock.patch('intergov.processors.callback_deliver.DeliverCallbackUseCase', autospec=True)
def test(DeliverCallbackUseCase, DeliveryOutboxRepo):
    processor = CallbacksDeliveryProcessor(CONNECTION_DATA)
    # checking proper initialization
    DeliveryOutboxRepo.assert_called_once_with(CONNECTION_DATA)
    DeliverCallbackUseCase.assert_called_once_with(DeliveryOutboxRepo.return_value)

    assert iter(processor) == processor

    use_case = DeliverCallbackUseCase.return_value
    use_case.execute.return_value = False
    assert next(processor) is False
    use_case.execute.return_value = True
    assert next(processor) is True
    use_case.execute.return_value = None
    assert next(processor) is None
    use_case.execute.return_value = True
    use_case.execute.side_effect = Exception('Test')
    assert next(processor) is None

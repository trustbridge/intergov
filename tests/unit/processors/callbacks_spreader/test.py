from unittest import mock
from intergov.processors.callbacks_spreader import CallbacksSpreaderProcessor
from tests.unit.repos.base.elasticmq.test import CONNECTION_DATA as ELASTICMQ_CONNECTION_DATA
from tests.unit.repos.base.minio.test import CONNECTION_DATA as MINIO_CONNECTION_DATA


@mock.patch('intergov.processors.callbacks_spreader.DeliveryOutboxRepo')
@mock.patch('intergov.processors.callbacks_spreader.NotificationsRepo')
@mock.patch('intergov.processors.callbacks_spreader.SubscriptionsRepo')
@mock.patch('intergov.processors.callbacks_spreader.DispatchMessageToSubscribersUseCase')
def test(DispatchMessageToSubscribersUseCase, SubscriptionsRepo, NotificationsRepo, DeliveryOutboxRepo):
    processor = CallbacksSpreaderProcessor(
        notifications_repo_conf=ELASTICMQ_CONNECTION_DATA,
        delivery_outbox_repo_conf=ELASTICMQ_CONNECTION_DATA,
        subscriptions_repo_conf=MINIO_CONNECTION_DATA
    )
    DeliveryOutboxRepo.assert_called_once()
    NotificationsRepo.assert_called_once()
    DeliveryOutboxRepo.assert_called_once()
    args, kwargs = SubscriptionsRepo.call_args_list[0]
    assert kwargs.items() <= MINIO_CONNECTION_DATA.items()
    args, kwargs = NotificationsRepo.call_args_list[0]
    assert kwargs.items() <= ELASTICMQ_CONNECTION_DATA.items()
    args, kwargs = DeliveryOutboxRepo.call_args_list[0]
    assert kwargs.items() <= ELASTICMQ_CONNECTION_DATA.items()
    DispatchMessageToSubscribersUseCase.assert_called_once_with(
        notifications_repo=NotificationsRepo.return_value,
        delivery_outbox_repo=DeliveryOutboxRepo.return_value,
        subscriptions_repo=SubscriptionsRepo.return_value
    )
    assert iter(processor) is processor
    use_case = DispatchMessageToSubscribersUseCase.return_value
    use_case.execute.return_value = True
    assert next(processor) is True
    use_case.execute.return_value = False
    assert next(processor) is False
    use_case.execute.return_value = None
    assert next(processor) is None
    use_case.execute.return_value = True
    use_case.execute.side_effect = Exception()
    assert next(processor) is None

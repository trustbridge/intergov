import pytest
from unittest import mock
import random
import uuid

from intergov.domain.wire_protocols import generic_discrete as protocol
from intergov.use_cases import DispatchMessageToSubscribersUseCase
from tests.unit.domain.wire_protocols import test_generic_message as test_protocol


@pytest.fixture
def valid_message_dicts():
    out = []
    for i in range(9):
        out.append(
            test_protocol._generate_msg_dict())
    return out


def test_delivery_enqueued(valid_message_dicts):
    message_dict = valid_message_dicts[0]
    notifications = mock.Mock()
    notifications.get_job.return_value = (1234, message_dict)
    delivery_outbox = mock.Mock()
    delivery_outbox.post_job.return_value = True
    subscriptions = mock.Mock()
    subscriptions.get_subscriptions_by_pattern.return_value = {mock.Mock(callback_url='https://foo.com/bar'), }
    use_case = DispatchMessageToSubscribersUseCase(
        notifications,
        delivery_outbox,
        subscriptions)
    use_case.execute()

    assert delivery_outbox.post_job.called
    assert notifications.delete.called


def test_notifications_empty_no_send(valid_message_dicts):
    message_dict = valid_message_dicts[0]
    m = protocol.Message.from_dict(message_dict)
    print(m)
    notifications = mock.Mock()
    notifications.get_job.return_value = ()
    delivery_outbox = mock.Mock()
    subscriptions = mock.Mock()
    subscriptions.get_subscriptions_by_pattern.return_value = {mock.Mock(callback_url='https://foo.com/bar'), }
    use_case = DispatchMessageToSubscribersUseCase(
        notifications,
        delivery_outbox,
        subscriptions)
    use_case.execute()

    assert not delivery_outbox.post_job.called


def test_delivery_outbox_post_fail_no_delete(valid_message_dicts):
    message_dict = valid_message_dicts[0]
    notifications = mock.Mock()
    notifications.get_job.return_value = (123, message_dict)
    delivery_outbox = mock.Mock()
    delivery_outbox.post_job.return_value = False  # post failed
    subscriptions = mock.Mock()
    subscriptions.get_subscriptions_by_pattern.return_value = {mock.Mock(callback_url='https://foo.com/bar'), }
    use_case = DispatchMessageToSubscribersUseCase(
        notifications,
        delivery_outbox,
        subscriptions)
    use_case.execute()

    assert not notifications.delete.called


def random_urls(*kwargs, **args):
    return [
        mock.Mock(callback_url="https://{}.{}/{}".format(
            uuid.uuid4(),
            random.choice(['com', 'net', 'org', 'com.au', 'gov.au']),
            uuid.uuid4()
        )) for x in range(6)]


def test_multiple_descriptions(valid_message_dicts):
    message_dict = valid_message_dicts[0]
    notifications = mock.Mock()
    notifications.get_job.return_value = (123, message_dict)
    delivery_outbox = mock.Mock()
    delivery_outbox.post_job.return_value = False  # post failed
    subscriptions = mock.Mock()
    subscriptions.get_subscriptions_by_pattern.side_effect = random_urls
    use_case = DispatchMessageToSubscribersUseCase(
        notifications,
        delivery_outbox,
        subscriptions)
    use_case.execute()

    assert not notifications.delete.called

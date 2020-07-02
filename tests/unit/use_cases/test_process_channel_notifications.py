import random
from unittest import mock

import pytest
import responses

from intergov.domain.wire_protocols.generic_discrete import Message
from intergov.repos.bc_inbox.elasticmq.elasticmqrepo import BCInboxRepo
from intergov.repos.channel_notifications_inbox import ChannelNotificationRepo
from intergov.use_cases.process_channel_notifications import (
    EnqueueChannelNotificationUseCase, ProcessChannelNotificationUseCase, ChannelNotFound
)


class TestEnqueueChannelNotificationUseCase:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.repo_mock = mock.Mock(spec=ChannelNotificationRepo)
        self.use_case = EnqueueChannelNotificationUseCase(self.repo_mock)

    def test_execute__should_put_a_job_into_queue(self):
        channel = {
            "Id": "b079bf38-c03d-4239-952b-d53b712bb07b",
        }
        self.use_case.execute(channel=channel, notification_payload={"id": "some-message-id-123"})
        job_payload = {
            'channel_id': 'b079bf38-c03d-4239-952b-d53b712bb07b',
            'notification_payload': {'id': 'some-message-id-123'},
            'attempt': 1
        }
        self.repo_mock.post_job.assert_called_once_with(job_payload, delay_seconds=0)

    @pytest.mark.parametrize("attempt, expected_delay", [(1, 0), (2, 26), (3, 52)])
    def test_retry__should_re_post_with_delay(self, attempt, expected_delay):
        random.seed(42)
        job_payload = {
            'channel_id': 'b079bf38-c03d-4239-952b-d53b712bb07b',
            'notification_payload': {'id': 'some-message-id-123'},
            'attempt': 1
        }
        self.use_case.retry(job_payload, attempt=attempt)

        job_payload['attempt'] = 2
        self.repo_mock.post_job.assert_called_once_with(job_payload, delay_seconds=expected_delay)


@pytest.mark.usefixtures("mocked_responses")
class TestProcessChannelNotificationUseCase:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.channel_notification_repo_mock = mock.Mock(spec=ChannelNotificationRepo)
        self.bc_inbox_repo_mock = mock.Mock(spec=BCInboxRepo)
        self.use_case = ProcessChannelNotificationUseCase(
            channel_notification_repo=self.channel_notification_repo_mock,
            bc_inbox_repo=self.bc_inbox_repo_mock,
            routing_table=[{
                "Id": "b079bf38-c03d-4239-952b-d53b712bb07b",
                "Name": "shared db channel to Australia",
                "Jurisdiction": "AU",
                "Predicate": "UN.CEFACT.",
                "ChannelUrl": "https://sharedchannel.services.devnet.trustbridge.io/",
                "ChannelAuth": "Cognito/JWT",
                "ChannelAuthDetails": {
                    "client_id": "XX",
                    "client_secret": "YY",
                    "token_endpoint": "https://xx/",
                    "scope": "https://sharedchannel.services.devnet.trustbridge.io/full"
                }
            },
            ]
        )

        self.message_payload = {
            'channel_id': 'b079bf38-c03d-4239-952b-d53b712bb07b',
            'notification_payload': {'id': '123'},
            'attempt': 1
        }
        self.channel_notification_repo_mock.get_job.return_value = 'queue-msg-id', self.message_payload

    @mock.patch('uuid.uuid4', return_value='11111111-1111-1111-1111-111111111')
    def test_execute__when_new_job__should_get_message_from_channel_and_enqueue_it_to_bc_inbox(self, uuid_mock):
        self.mocked_responses.add(responses.GET, url='https://sharedchannel.services.devnet.trustbridge.io/messages/123', json={
            'id': 123,
            'status': 'confirmed',
            'message': {
                "sender": "CN",
                "receiver": "AU",
                "subject": "AU.abn0000000000.XXXX-XXXXX-XXXXX-XXXXXX",
                "obj": "3gehKTiDMB7r1LM3731nadxJM1n5Vx3eBTvbd9X2P6umuWFjG8Aw",
                "predicate": "UN.CEFACT.Trade.CertificateOfOrigin.created",
            }
        })

        self.use_case.execute()
        assert self.bc_inbox_repo_mock.post.call_count == 1
        args, kwargs = self.bc_inbox_repo_mock.post.call_args_list[0]
        message = args[0]
        assert isinstance(message, Message)
        assert message.to_dict() == {
            'sender': 'CN',
            'receiver': 'AU',
            "subject": "AU.abn0000000000.XXXX-XXXXX-XXXXX-XXXXXX",
            'obj': '3gehKTiDMB7r1LM3731nadxJM1n5Vx3eBTvbd9X2P6umuWFjG8Aw',
            'predicate': 'UN.CEFACT.Trade.CertificateOfOrigin.created',
            'sender_ref': '11111111-1111-1111-1111-111111111',
            'status': 'received',
        }

    def test_execute__when_api_failure__should_retry(self):
        self.mocked_responses.add(
            responses.GET,
            url='https://sharedchannel.services.devnet.trustbridge.io/messages/123',
            status=500
        )
        random.seed(42)
        self.use_case.execute()
        assert not self.bc_inbox_repo_mock.post.called
        self.channel_notification_repo_mock.post_job.assert_called_once_with(
            {
                'channel_id': 'b079bf38-c03d-4239-952b-d53b712bb07b',
                'notification_payload': {'id': '123'},
                'attempt': 2
            },
            delay_seconds=26
        )

    def test_execute__when_no_such_channel_in_routing_table__should_raise_error(self):
        self.message_payload['channel_id'] = 'not-exists'
        with pytest.raises(ChannelNotFound):
            self.use_case.execute()

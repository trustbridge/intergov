from unittest import mock
from intergov.domain.wire_protocols.generic_discrete import (
    Message,
    STATUS_PENDING,
    STATUS_ACCEPTED,
    STATUS_KEY
)

from intergov.use_cases import PatchMessageMetadataUseCase
from tests.unit.domain.wire_protocols.test_generic_message import (
    _generate_msg_dict
)


SENDER = "AU"
SENDER_REF = "xxxxx-xxxxx-xxxxx"

MESSAGE_REF = f"{SENDER}:{SENDER_REF}"


def test_patch_only_status_and_update_skip_for_equal_status():

    # testing only status update / ingoring other payload fields
    payload = _generate_msg_dict()
    payload[STATUS_KEY] = STATUS_PENDING
    message = Message.from_dict(payload)

    notifications_repo = mock.MagicMock()
    message_lake_repo = mock.MagicMock()
    message_lake_repo.get.return_value = message

    new_payload = _generate_msg_dict()
    new_payload[STATUS_KEY] = STATUS_ACCEPTED
    uc = PatchMessageMetadataUseCase(message_lake_repo, notifications_repo)
    uc.execute(
        MESSAGE_REF,
        new_payload
    )

    message_lake_repo.get.assert_called()
    message_lake_repo.update_metadata.assert_called_once_with(
        SENDER,
        SENDER_REF,
        {STATUS_KEY: new_payload[STATUS_KEY]}
    )
    notifications_repo.post_job.assert_called()

    # testing ingoring update for the equal status values
    notifications_repo.reset_mock()
    message_lake_repo.reset_mock()

    uc.execute(
        MESSAGE_REF,
        payload
    )

    message_lake_repo.get.assert_called()
    message_lake_repo.update_metadata.assert_not_called()
    notifications_repo.post_job.assert_not_called()

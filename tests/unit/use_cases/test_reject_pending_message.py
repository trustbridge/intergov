from unittest import mock
import pytest

from intergov.use_cases import RejectPendingMessageUseCase
from intergov.domain.wire_protocols.generic_discrete import (
    Message,
    SENDER_REF_KEY
)
from tests.unit.domain.wire_protocols.test_generic_message import (
    _generate_msg_dict
)


def _generate_msg(**kwargs):
    return Message.from_dict(_generate_msg_dict(**kwargs))


def test_execute():
    rejected_message_repo = mock.MagicMock()
    message_lake_repo = mock.MagicMock()

    # testing successful execution
    payload = _generate_msg(
        **{
            SENDER_REF_KEY: "xxxx-xxxx-xxxx"
        }
    )
    queue_id = 1

    rejected_message_repo.get.return_value = (queue_id, payload,)
    rejected_message_repo.delete.return_value = True

    uc = RejectPendingMessageUseCase(
        rejected_message_repo,
        message_lake_repo
    )

    assert uc.execute()

    rejected_message_repo.get.assert_called_once()
    message_lake_repo.update_metadata.assert_called_with(
        payload.sender,
        payload.sender_ref,
        {
            'status': 'rejected'
        }
    )
    rejected_message_repo.delete.assert_called_once_with(
        queue_id
    )

    # testing no rejected messages in queue
    rejected_message_repo.reset_mock()
    message_lake_repo.reset_mock()

    rejected_message_repo.get.return_value = None

    assert uc.execute() is None

    rejected_message_repo.get.assert_called_once()
    message_lake_repo.update_metadata.assert_not_called()
    rejected_message_repo.delete.assert_not_called()

    # testing unable to update status
    rejected_message_repo.reset_mock()
    message_lake_repo.reset_mock()

    message_lake_repo.update_metadata.side_effect = Exception("Reason")
    with pytest.raises(Exception) as e:
        uc.execute()
        assert str(e) == "Unable to update message status. Reason: {}".format(
            message_lake_repo.update_metadata.side_effect
        )
        rejected_message_repo.get.assert_called_once()
        message_lake_repo.update_metadata.assert_called_once()
        rejected_message_repo.delete.assert_not_called()
    message_lake_repo.update_metadata.side_effect = None

    # testing not deleted
    rejected_message_repo.reset_mock()
    message_lake_repo.reset_mock()

    payload = _generate_msg(sender_ref="x")
    rejected_message_repo.delete.return_value = None
    rejected_message_repo.get.return_value = (queue_id, payload)

    assert not uc.execute()

    rejected_message_repo.get.assert_called_once()
    message_lake_repo.update_metadata.assert_called_once()
    rejected_message_repo.delete.assert_called_once_with(
        queue_id
    )

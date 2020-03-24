from unittest import mock
from intergov.processors.rejected_status_updater import RejectedStatusUpdater


REJECTED_MESSAGE_REPO_CONF = {
    'test': 'rejected-messages-repo-conf'
}

MESSAGE_LAKE_REPO_CONF = {
    'test': 'message-lake-repo-conf'
}


@mock.patch('intergov.processors.rejected_status_updater.MessageLakeRepo')
@mock.patch('intergov.processors.rejected_status_updater.RejectedMessagesRepo')
@mock.patch('intergov.processors.rejected_status_updater.RejectPendingMessageUseCase')
def test(
    RejectPendingMessageUseCase,
    RejectedMessagesRepo,
    MessageLakeRepo
):

    updater = RejectedStatusUpdater(
        rejected_message_repo_conf=REJECTED_MESSAGE_REPO_CONF,
        message_lake_repo_conf=MESSAGE_LAKE_REPO_CONF
    )

    for Repo, conf in [
        (RejectedMessagesRepo, REJECTED_MESSAGE_REPO_CONF,),
        (MessageLakeRepo, MESSAGE_LAKE_REPO_CONF,)
    ]:
        Repo.assert_called_once()
        args, kwargs = Repo.call_args_list[0]
        assert kwargs.items() <= conf.items()
    RejectPendingMessageUseCase.assert_called_once_with(
        rejected_message_repo=RejectedMessagesRepo.return_value,
        message_lake_repo=MessageLakeRepo.return_value
    )
    use_case = RejectPendingMessageUseCase.return_value
    use_case.execute.side_effect = [
        True,
        False,
        None,
        Exception()
    ]
    assert iter(updater) is updater
    assert next(updater) is True
    assert next(updater) is False
    assert next(updater) is None
    assert next(updater) is None

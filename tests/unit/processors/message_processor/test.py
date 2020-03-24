from unittest import mock
from intergov.processors.message_processor import InboundMessageProcessor


BC_INBOX_REPO_CONF = {
    'test': 'bc-inbox-repo-conf'
}

MESSAGE_LAKE_REPO_CONF = {
    'test': 'message-lake-repo-conf'
}

OBJECT_ACL_REPO_CONF = {
    'test': 'object-acl-repo-conf'
}

OBJECT_RETRIEVAL_REPO_CONF = {
    'test': 'object-retrieval-repo-conf'
}

NOTIFICATIONS_REPO_CONF = {
    'test': 'notifications-repo-conf'
}

BLOCKCHAIN_OUTBOX_REPO_CONF = {
    'test': 'blockchain-outbox-repo-conf'
}


@mock.patch('intergov.processors.message_processor.BCInboxRepo')
@mock.patch('intergov.processors.message_processor.ApiOutboxRepo')
@mock.patch('intergov.processors.message_processor.MessageLakeRepo')
@mock.patch('intergov.processors.message_processor.ObjectACLRepo')
@mock.patch('intergov.processors.message_processor.ObjectRetrievalRepo')
@mock.patch('intergov.processors.message_processor.NotificationsRepo')
@mock.patch('intergov.processors.message_processor.ProcessMessageUseCase')
def test(
    ProcessMessageUseCase,
    NotificationsRepo,
    ObjectRetrievalRepo,
    ObjectACLRepo,
    MessageLakeRepo,
    ApiOutboxRepo,
    BCInboxRepo
):

    processor = InboundMessageProcessor(
        bc_inbox_repo_conf=BC_INBOX_REPO_CONF,
        message_lake_repo_conf=MESSAGE_LAKE_REPO_CONF,
        object_acl_repo_conf=OBJECT_ACL_REPO_CONF,
        object_retrieval_repo_conf=OBJECT_RETRIEVAL_REPO_CONF,
        notifications_repo_conf=NOTIFICATIONS_REPO_CONF,
        blockchain_outbox_repo_conf=BLOCKCHAIN_OUTBOX_REPO_CONF
    )

    NotificationsRepo.assert_called_once()
    ObjectRetrievalRepo.assert_called_once()
    ObjectACLRepo.assert_called_once()
    MessageLakeRepo.assert_called_once()
    ApiOutboxRepo.assert_called_once()
    BCInboxRepo.assert_called_once()

    for Repo, conf in [
        (NotificationsRepo, NOTIFICATIONS_REPO_CONF,),
        (ObjectRetrievalRepo, OBJECT_RETRIEVAL_REPO_CONF,),
        (ObjectACLRepo, OBJECT_ACL_REPO_CONF,),
        (MessageLakeRepo, MESSAGE_LAKE_REPO_CONF,),
        (ApiOutboxRepo, BLOCKCHAIN_OUTBOX_REPO_CONF,),
        (BCInboxRepo, BC_INBOX_REPO_CONF,)
    ]:
        Repo.assert_called_once()
        args, kwargs = Repo.call_args_list[0]
        assert kwargs.items() <= conf.items()

    ProcessMessageUseCase.assert_called_once_with(
        country='AU',
        bc_inbox_repo=BCInboxRepo.return_value,
        message_lake_repo=MessageLakeRepo.return_value,
        object_acl_repo=ObjectACLRepo.return_value,
        object_retreval_repo=ObjectRetrievalRepo.return_value,
        notifications_repo=NotificationsRepo.return_value,
        blockchain_outbox_repo=ApiOutboxRepo.return_value,
    )

    assert iter(processor) is processor
    use_case = ProcessMessageUseCase.return_value
    use_case.execute.side_effect = [
        True,
        False,
        None,
        Exception()
    ]
    assert next(processor) is True
    assert next(processor) is False
    assert next(processor) is None
    assert next(processor) is None

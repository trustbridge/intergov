import pytest
from unittest import mock

from intergov.domain.wire_protocols import generic_discrete as protocol
from intergov.use_cases import retrieve_and_store_foreign_documents as uc
from tests.unit.domain.wire_protocols import test_generic_message as test_protocol


@pytest.fixture
def valid_message_dicts():
    out = []
    for i in range(9):
        out.append(
            test_protocol._generate_msg_dict())
    return out


def test_empty_queue(valid_message_dicts):
    object_retrieval_repo = mock.Mock()
    object_retrieval_repo.get.return_value = False
    object_lake_repo = mock.Mock()
    foreign_object_repo = mock.Mock()

    use_case = uc.RetrieveAndStoreForeignDocumentsUseCase(
        object_retrieval_repo,
        object_lake_repo,
        foreign_object_repo
    )

    assert not use_case.execute()
    assert not object_lake_repo.post.called
    assert not foreign_object_repo.get.called
    assert not object_retrieval_repo.delete.called


def test_happy_case(valid_message_dicts):
    message_dict = valid_message_dicts[0]
    m = protocol.Message.from_dict(message_dict)
    object_retrieval_repo = mock.Mock()
    object_retrieval_repo.get.return_value = (8765, m)
    object_lake_repo = mock.Mock()
    foreign_object_repo = mock.Mock()

    use_case = uc.RetrieveAndStoreForeignDocumentsUseCase(
        object_retrieval_repo,
        object_lake_repo,
        foreign_object_repo
    )

    assert use_case.execute()
    assert foreign_object_repo.get.called
    assert object_lake_repo.post.called
    assert object_retrieval_repo.delete.called


def test_fetch_fails(valid_message_dicts):
    message_dict = valid_message_dicts[0]
    m = protocol.Message.from_dict(message_dict)
    object_retrieval_repo = mock.Mock()
    object_retrieval_repo.get.return_value = (8765, m)
    object_lake_repo = mock.Mock()
    foreign_object_repo = mock.Mock()
    foreign_object_repo.get.return_value = False

    use_case = uc.RetrieveAndStoreForeignDocumentsUseCase(
        object_retrieval_repo,
        object_lake_repo,
        foreign_object_repo
    )

    assert not use_case.execute()
    assert foreign_object_repo.get.called
    assert not object_lake_repo.post.called
    assert not object_retrieval_repo.delete.called


def test_object_lake_post_fails(valid_message_dicts):
    message_dict = valid_message_dicts[0]
    m = protocol.Message.from_dict(message_dict)
    object_retrieval_repo = mock.Mock()
    object_retrieval_repo.get.return_value = (8765, m)
    object_lake_repo = mock.Mock()
    object_lake_repo.post.return_value = False
    foreign_object_repo = mock.Mock()

    use_case = uc.RetrieveAndStoreForeignDocumentsUseCase(
        object_retrieval_repo,
        object_lake_repo,
        foreign_object_repo
    )

    assert not use_case.execute()
    assert foreign_object_repo.get.called
    assert object_lake_repo.post.called
    assert not object_retrieval_repo.delete.called

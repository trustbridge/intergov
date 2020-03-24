# import pytest
# from unittest import mock

# from intergov.domain.wire_protocols import generic_discrete as protocol
# from intergov.use_cases import enqueue_posted_message as uc
# from tests.domain.wire_protocols import test_generic_message as test_protocol


# @pytest.fixture
# def valid_message_dicts():
#     out = []
#     for i in range(9):
#         out.append(
#             test_protocol._generate_msg_dict())
#     return out


# def test_enque_true_if_inbox_get_returns_something(valid_message_dicts):
#     message_dict = valid_message_dicts[0]
#     inbox = mock.Mock()
#     inbox.get.return_value = (1234, protocol.Message.from_dict(message_dict))
#     outbox = mock.Mock()
#     outbox.post.return_value = True

#     use_case = uc.EnqueuePostedMessageUseCase(inbox, outbox)
#     retval = use_case.execute()

#     assert retval  # true because inbox not empty


# def test_enque_false_if_inbox_get_returns_nothing(valid_message_dicts):
#     inbox = mock.Mock()
#     inbox.get.return_value = False
#     outbox = mock.Mock()

#     use_case = uc.EnqueuePostedMessageUseCase(inbox, outbox)
#     retval = use_case.execute()

#     assert not retval  # false because inbox empty


# def test_sucessful_enque_deletes_from_inbox(valid_message_dicts):
#     message_dict = valid_message_dicts[0]
#     inbox = mock.Mock()
#     inbox.get.return_value = (1234, protocol.Message.from_dict(message_dict))
#     outbox = mock.Mock()
#     outbox.post.return_value = True

#     use_case = uc.EnqueuePostedMessageUseCase(inbox, outbox)
#     use_case.execute()

#     assert inbox.delete.called


# def test_unsucessful_enque_does_not_delete_from_inbox(valid_message_dicts):
#     message_dict = valid_message_dicts[0]
#     inbox = mock.Mock()
#     inbox.get.return_value = (1234, protocol.Message.from_dict(message_dict))
#     outbox = mock.Mock()
#     outbox.post.return_value = False

#     use_case = uc.EnqueuePostedMessageUseCase(inbox, outbox)
#     use_case.execute()

#     assert not inbox.delete.called

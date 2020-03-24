# from unittest import mock
# from intergov.use_cases import subscribe_to_messages as uc


# def test_subscribe_OK():
#     repo = mock.Mock()
#     repo.create_subscription.return_value = True
#     user = mock.Mock()
#     channel_filter = mock.Mock()
#     callback = mock.Mock()

#     use_case = uc.SubscribeToMessagesUseCase(
#         repo,
#         user,
#         channel_filter,
#         callback)
#     assert use_case.execute()


# def test_invalid_user():
#     repo = mock.Mock()
#     user = mock.Mock()
#     user.is_valid.return_value = False
#     channel_filter = mock.Mock()
#     callback = mock.Mock()

#     use_case = uc.SubscribeToMessagesUseCase(
#         repo,
#         user,
#         channel_filter,
#         callback)
#     assert not use_case.execute()


# def test_already_subscribed_OK():
#     repo = mock.Mock()
#     repo.subscription_exists.return_value = True
#     user = mock.Mock()
#     channel_filter = mock.Mock()
#     callback = mock.Mock()

#     use_case = uc.SubscribeToMessagesUseCase(
#         repo,
#         user,
#         channel_filter,
#         callback)
#     assert use_case.execute()

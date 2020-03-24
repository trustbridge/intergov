# class SubscribeToMessagesUseCase:

#     def __init__(self, repo, user, channel_filter, callback):
#         self.repo = repo
#         self.user = user
#         self.channel_filter = channel_filter
#         self.callback = callback

#     def execute(self):
#         if not self.user.is_valid():
#             return False
#         if self.repo.subscription_exists(
#                 self.user,
#                 self.channel_filter,
#                 self.callback):
#             return True
#         return self.repo.create_subscription(
#             self.user,
#             self.channel_filter,
#             self.callback)

from intergov.monitoring import statsd_timer


class SubscriptionRegisterUseCase:
    """
    Used by the subscription API

    Initialised with the subscription repo,
    saves url, predicate(pattern), expiration to the storage.
    """

    def __init__(self, subscriptions_repo):
        self.subscriptions = subscriptions_repo

    @statsd_timer("usecase.SubscriptionRegisterUseCase.execute")
    def execute(self, url, pattern, expiration):
        # this operation deletes all previous subscription for given url and pattern
        # and replaces them with new one. Techically it's create or update operation
        posted = self.subscriptions.post(url, pattern, expiration)
        if not posted:
            return None
        return True

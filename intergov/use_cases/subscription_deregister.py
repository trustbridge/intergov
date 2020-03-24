from intergov.monitoring import statsd_timer


class SubscriptionDeregisterUseCase:
    """
    Used by the subscription API

    on user's request removes the subscription to given url for given pattern
    """

    def __init__(self, subscriptions_repo):
        self.subscriptions = subscriptions_repo

    @statsd_timer("usecase.SubscriptionDeregisterUseCase.execute")
    def execute(self, url, pattern):
        return self.subscriptions.delete(url, pattern) > 0

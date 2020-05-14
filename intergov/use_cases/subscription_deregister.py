from libtrustbridge.websub.domain import Pattern
from libtrustbridge.websub.repos import SubscriptionsRepo

from intergov.monitoring import statsd_timer


class SubscriptionDeregisterUseCase:
    """
    Used by the subscription API

    on user's request removes the subscription to given url for given pattern
    """

    def __init__(self, subscriptions_repo: SubscriptionsRepo):
        self.subscriptions_repo = subscriptions_repo

    @statsd_timer("usecase.SubscriptionDeregisterUseCase.execute")
    def execute(self, url, predicate):
        pattern = Pattern(predicate=predicate)
        self.subscriptions_repo.bulk_delete([pattern.to_key(url)])


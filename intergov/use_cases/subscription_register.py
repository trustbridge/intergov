from libtrustbridge.websub.domain import Pattern
from libtrustbridge.websub.repos import SubscriptionsRepo

from intergov.monitoring import statsd_timer


class SubscriptionRegisterUseCase:
    """
    Used by the subscription API

    Initialised with the subscription repo,
    saves url, predicate(pattern), expiration to the storage.
    """

    def __init__(self, subscriptions_repo: SubscriptionsRepo):
        self.subscriptions_repo = subscriptions_repo

    @statsd_timer("usecase.SubscriptionRegisterUseCase.execute")
    def execute(self, url, predicate, expiration=None):
        # this operation deletes all previous subscription for given url and pattern
        # and replaces them with new one. Techically it's create or update operation

        posted = self.subscriptions_repo.subscribe_by_pattern(Pattern(predicate), url,  expiration)
        if not posted:
            return None
        return True

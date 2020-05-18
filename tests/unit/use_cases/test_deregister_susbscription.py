import pytest
from unittest import mock
from intergov.use_cases import SubscriptionDeregisterUseCase

CALLBACK = 'http://url.com/callback'
USE_CASE_ARGS = (CALLBACK, "UN.CEFACT.*")


def test_execute():
    repo = mock.MagicMock()
    repo.get_subscriptions_by_pattern.return_value = {mock.Mock(callback_url=CALLBACK)}
    uc = SubscriptionDeregisterUseCase(repo)
    uc.execute(*USE_CASE_ARGS)

    repo.bulk_delete.side_effect = Exception("Hey")
    with pytest.raises(Exception) as e:
        uc.execute(*USE_CASE_ARGS)
        assert str(e) == str(repo.bulk_delete.side_effect)

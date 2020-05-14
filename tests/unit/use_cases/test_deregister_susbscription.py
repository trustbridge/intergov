import pytest
from unittest import mock
from intergov.use_cases import SubscriptionDeregisterUseCase

USE_CASE_ARGS = ("http://url.com/callback", "UN.CEFACT.*")


def test_execute():
    repo = mock.MagicMock()

    repo.delete.return_value = 1
    uc = SubscriptionDeregisterUseCase(repo)
    assert uc.execute(*USE_CASE_ARGS)

    repo.delete.side_effect = Exception("Hey")
    with pytest.raises(Exception) as e:
        uc.execute(*USE_CASE_ARGS)
        assert str(e) == str(repo.post.side_effect)

    repo.delete.side_effect = None
    repo.delete.return_value = 0
    assert not uc.execute(*USE_CASE_ARGS)
    assert repo.delete.call_count == 3

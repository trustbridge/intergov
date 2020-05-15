import pytest
from unittest import mock
from intergov.use_cases import SubscriptionRegisterUseCase

USE_CASE_ARGS = ("http://url.com/callback", "UN.CEFACT.*", 1000,)


def test_execute():
    repo = mock.MagicMock()

    uc = SubscriptionRegisterUseCase(repo)
    assert uc.execute(*USE_CASE_ARGS)

    repo.subscribe_by_pattern.side_effect = Exception("Hey")
    with pytest.raises(Exception) as e:
        uc.execute(*USE_CASE_ARGS)
        assert str(e) == str(repo.post.side_effect)


import pytest
from unittest import mock
from intergov.use_cases import SubscriptionRegisterUseCase

USE_CASE_ARGS = ("http://url.com/callback", "UN.CEFACT.*", 1000,)


def test_exectute():
    repo = mock.MagicMock()

    repo.post.return_value = True
    uc = SubscriptionRegisterUseCase(repo)
    assert uc.execute(*USE_CASE_ARGS)

    repo.post.side_effect = Exception("Hey")
    with pytest.raises(Exception) as e:
        uc.execute(*USE_CASE_ARGS)
        assert str(e) == str(repo.post.side_effect)

    repo.post.side_effect = None
    repo.post.return_value = None
    assert uc.execute(*USE_CASE_ARGS) is None
    assert repo.post.call_count == 3

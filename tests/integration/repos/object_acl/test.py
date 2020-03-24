import pytest
from intergov.conf import env_s3_config
from intergov.repos.object_acl import ObjectACLRepo
from tests.unit.domain.wire_protocols.test_generic_message import (
    _generate_msg_object
)

CONF = env_s3_config('TEST')


def test():
    repo = ObjectACLRepo(CONF)
    repo._unsafe_clear_for_test()
    assert repo._unsafe_is_empty_for_test()

    message = _generate_msg_object()
    obj = str(message.obj)
    receiver = str(message.receiver)

    # testing post actions
    assert repo.post(message)
    assert repo.allow_access_to(obj, receiver)
    # no filters
    with pytest.raises(Exception):
        repo.search()

    # invalid filters
    with pytest.raises(Exception):
        repo.search({'abrakadabra': 'value'})

    search_result = repo.search({'object__eq': obj})
    assert search_result
    assert message.receiver in search_result
    assert not repo.search({'object__eq': 'something_strange'})

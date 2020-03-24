from intergov.domain.channel_filters import generic_message_filter as gmf
from intergov.domain.wire_protocols import generic_discrete as protocol

kwargs = {
    "sender": "AU",
    "receiver": "CN",
    "subject": "x",
    "obj": "y",
    "predicate": "z"
}


def test_allow_any():
    f = gmf.DiscreteGenericMessageFilter()
    for k in kwargs.keys():
        f.allow_any(k)
    m = protocol.Message(**kwargs)
    assert not f.screen_message(m)


def test_allow_none():
    f = gmf.DiscreteGenericMessageFilter()
    m = protocol.Message(**kwargs)
    assert f.screen_message(m)


def test_whitelist_one_attr():
    m = protocol.Message(**kwargs)
    for test_attr in kwargs.keys():
        f = gmf.DiscreteGenericMessageFilter()
        for k in kwargs.keys():
            if k != test_attr:
                f.allow_any(k)
            else:
                f.whitelist(k, kwargs[k])
        assert not f.screen_message(m)


def test_blacklist():
    m = protocol.Message(**kwargs)
    for test_attr in kwargs.keys():
        f = gmf.DiscreteGenericMessageFilter()
        for k in kwargs.keys():
            if k != test_attr:
                f.allow_any(k)
            else:
                f.blacklist(k, kwargs[k])
            assert f.screen_message(m)

        f = gmf.DiscreteGenericMessageFilter()
        for k in kwargs.keys():
            f.allow_any(k)
            if k == test_attr:
                f.blacklist(k, kwargs[k])
            assert f.screen_message(m)

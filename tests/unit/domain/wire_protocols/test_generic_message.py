import random
import uuid
import copy
import json
import multihash

from intergov.domain.jurisdiction import Jurisdiction
from intergov.domain.wire_protocols import generic_discrete as gd
from intergov.domain import uri as u
from intergov.serializers import generic_discrete_message as ser


def _random_multihash():
    digest = str(uuid.uuid4()).encode()
    return multihash.to_b58_string(multihash.encode(digest, 'sha2-256'))


def _generate_msg_dict(**kwargs):
    # test predicates must have some dots in them,
    # so that we can test the predicate__wild filter
    # tmp = str(uuid.uuid4())[:-4]
    # predicate = str("http://predicate/{}.{}.{}.{}".format(
    #         tmp[0:5],
    #         tmp[5:10],
    #         tmp[10:20],
    #         tmp[20:]))
    short_countries_list = ['AU', 'CN']
    sender = random.choice(short_countries_list)
    short_countries_list.remove(sender)
    receiver = random.choice(short_countries_list)
    predicate_parts = []
    for i in range(4):
        predicate_parts.append(_random_multihash()[:4])
    predicate = ".".join(predicate_parts)
    subject = _random_multihash()
    obj = _random_multihash()
    return {
        "sender": sender,
        "receiver": receiver,
        "subject": subject,
        "obj": obj,
        "predicate": predicate,
        **kwargs
    }


def _generate_msg_object(**kwargs):
    return gd.Message.from_dict(_generate_msg_dict(**kwargs))


def _remove_message_params(data, keys=[], copy_data=True, set_none=False):
    if copy_data:
        data = copy.deepcopy(data)
    for key in keys:
        if set_none:
            data[key] = None
        else:
            del data[key]
    return data


def _remove_required_message_params(data, index=-1, indexes=[]):
    if index >= 0:
        indexes.append(index)
    return _remove_message_params(data, keys=[gd.Message.required_attrs[i] for i in indexes])


def _encode_message_dict(data):
    return json.dumps(data, cls=ser.MessageJSONEncoder)


def _diff_message_dicts(left, right, keys=[]):
    diff = []
    for key in keys:
        l_val = left.get(key)
        r_val = right.get(key)
        if l_val != r_val:
            diff.append({
                'key': key,
                'left': l_val,
                'right': r_val
            })
    return diff


def _generate_message_params():
    msg_dict = _generate_msg_dict()

    A = Jurisdiction(msg_dict["sender"])
    B = Jurisdiction(msg_dict["receiver"])
    subject = u.URI(msg_dict["subject"])
    obj = u.URI(msg_dict["obj"])
    predicate = u.URI(msg_dict["predicate"])

    return (A, B, subject, obj, predicate)


def _generate_invalid_uri_list():
    return (None, "invalid", 42)


def test_message_from_dict():
    adict = _generate_msg_dict()
    msg = gd.Message.from_dict(adict)
    assert msg.is_valid()


def test_message_to_dict():
    adict = _generate_msg_dict()
    msg = gd.Message.from_dict(adict)
    assert msg.to_dict() == adict


def test_message_comparison():
    adict = _generate_msg_dict()
    m1 = gd.Message.from_dict(adict)
    m2 = gd.Message.from_dict(adict)
    assert m1 == m2


def test_validation_OK():
    A, B, subject, obj, predicate = _generate_message_params()
    msg = gd.Message(
        sender=A,
        receiver=B,
        subject=subject,
        obj=obj,
        predicate=predicate)
    assert msg.is_valid()


def test_validation_invalid_no_sender():
    A, B, subject, obj, predicate = _generate_message_params()
    msg = gd.Message(
        receiver=B,
        subject=subject,
        obj=obj,
        predicate=predicate)
    assert not msg.is_valid()


def test_validation_invalid_sender():
    A, B, subject, obj, predicate = _generate_message_params()
    for x in _generate_invalid_uri_list():
        A = x
        msg = gd.Message(
            sender=A,
            receiver=B,
            subject=subject,
            obj=obj,
            predicate=predicate)
        assert not msg.is_valid()


def test_validation_invalid_no_reciever():
    A, B, subject, obj, predicate = _generate_message_params()
    msg = gd.Message(
        sender=A,
        subject=subject,
        obj=obj,
        predicate=predicate)
    assert not msg.is_valid()


def test_validation_invalid_receiver():
    A, B, subject, obj, predicate = _generate_message_params()
    for x in _generate_invalid_uri_list():
        B = x
        msg = gd.Message(
            sender=A,
            receiver=B,
            subject=subject,
            obj=obj,
            predicate=predicate)
        assert not msg.is_valid()


def test_validation_invalid_no_subject():
    A, B, subject, obj, predicate = _generate_message_params()
    msg = gd.Message(
        sender=A,
        receiver=B,
        obj=obj,
        predicate=predicate)
    assert not msg.is_valid()


def test_validation_invalid_no_obj():
    A, B, subject, obj, predicate = _generate_message_params()
    msg = gd.Message(
        sender=A,
        receiver=B,
        subject=subject,
        predicate=predicate)
    assert not msg.is_valid()


def test_validation_invalid_obj():
    A, B, subject, obj, predicate = _generate_message_params()
    for x in _generate_invalid_uri_list():
        obj = x
        msg = gd.Message(
            sender=A,
            receiver=B,
            subject=subject,
            obj=obj,
            predicate=predicate)
        assert not msg.is_valid()


def test_validation_invalid_no_predicate():
    A, B, subject, obj, predicate = _generate_message_params()
    msg = gd.Message(
        sender=A,
        receiver=B,
        subject=subject,
        obj=obj)
    assert not msg.is_valid()


def test_validation_invalid_predicate():
    A, B, subject, obj, predicate = _generate_message_params()
    for x in _generate_invalid_uri_list():
        predicate = x
        msg = gd.Message(
            sender=A,
            receiver=B,
            subject=subject,
            obj=obj,
            predicate=predicate)
        assert not msg.is_valid()


def test_validation_bogus_parameter():
    A, B, subject, obj, predicate = _generate_message_params()
    msg = gd.Message(
        bogus=True,
        sender=A,
        receiver=B,
        subject=subject,
        obj=obj)
    assert not msg.is_valid()

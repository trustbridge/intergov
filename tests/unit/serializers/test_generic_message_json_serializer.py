import json
import uuid

from intergov.serializers import generic_discrete_message as ser
from intergov.domain.wire_protocols import generic_discrete as gd
from intergov.domain import country as c
from intergov.domain import uri as u


def test_serialise_mesage():
    tx = "AU"
    rx = "CN"
    s = str(uuid.uuid4())
    t = str(uuid.uuid4())
    p = str(uuid.uuid4())

    msg = gd.Message(
        sender=c.Country(tx),
        receiver=c.Country(rx),
        subject=u.URI(s),
        obj=u.URI(t),
        predicate=u.URI(p))

    expected_json = """
       {{
            "sender": "{}",
            "receiver": "{}",
            "subject": "{}",
            "obj": "{}",
            "predicate": "{}"
       }}
    """.format(tx, rx, s, t, p)

    msg_json = json.dumps(msg, cls=ser.MessageJSONEncoder)

    assert json.loads(msg_json) == json.loads(expected_json)

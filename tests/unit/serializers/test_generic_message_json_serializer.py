import json
import uuid

from intergov.domain.wire_protocols import generic_discrete as gd
from intergov.domain.jurisdiction import Jurisdiction
from intergov.domain.uri import URI
from intergov.serializers import generic_discrete_message as ser


def test_serialize_message():
    tx = "AU"
    rx = "CN"
    s = str(uuid.uuid4())
    t = str(uuid.uuid4())
    p = str(uuid.uuid4())

    msg = gd.Message(
        sender=Jurisdiction(tx),
        receiver=Jurisdiction(rx),
        subject=URI(s),
        obj=URI(t),
        predicate=URI(p))

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

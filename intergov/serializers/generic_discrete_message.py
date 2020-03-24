import json


class MessageJSONEncoder(json.JSONEncoder):

    def default(self, o):
        try:
            to_serialize = {
                # TODO: alphabetical order of the fields
                "sender": str(o.sender),
                "receiver": str(o.receiver),
                "subject": str(o.subject),
                "obj": str(o.obj),
                "predicate": str(o.predicate),
            }
            if o.sender_ref:
                to_serialize["sender_ref"] = str(o.sender_ref)
            if o.status:
                to_serialize["status"] = str(o.status)
            return to_serialize

        except AttributeError:
            return super().default(o)

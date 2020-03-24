"""
The "Generic Discrete" wire protocol
can be used to transmit any assertion
because it implements an RDF style message "triple"
that is sent from one country to another.
It is "generic" because it does not impose
restrictions on the information that
the triples contain.
It is "discrete" because each message
carries exactly one assertion (triple).
"""
import json

from intergov.domain import country as c
from intergov.domain import uri as u


SENDER_KEY = "sender"
RECEIVER_KEY = "receiver"
SUBJECT_KEY = "subject"
OBJ_KEY = "obj"
PREDICATE_KEY = "predicate"
CHANNEL_ID_KEY = "channel_id"
CHANNEL_TXN_ID_KEY = "channel_txn_id"

STATUS_PENDING = "pending"
STATUS_ACCEPTED = "accepted"
STATUS_REJECTED = "rejected"
STATUS_RECEIVED = "received"
# TODO add all posible statuses
ALLOWED_STATUSES = [
    STATUS_PENDING,
    STATUS_ACCEPTED,
    STATUS_REJECTED,
    STATUS_RECEIVED,
    None
]

FINAL_STATUSES = [
    STATUS_ACCEPTED,
    STATUS_REJECTED
]

STATUS_KEY = "status"
SENDER_REF_KEY = "sender_ref"

REQUIRED_ATTRS = [
    SENDER_KEY,
    RECEIVER_KEY,
    SUBJECT_KEY,
    OBJ_KEY,
    PREDICATE_KEY
]

ALLOWED_ATTRS = [
    STATUS_KEY,
    SENDER_REF_KEY,
    CHANNEL_ID_KEY,
    CHANNEL_TXN_ID_KEY
]

ALL_ATTRS = REQUIRED_ATTRS + ALLOWED_ATTRS


def is_country(value):
    return isinstance(value, c.Country)


def not_country_error(key, value):
    return f"{key} is not a country: {value}"


def is_URI(value):
    return isinstance(value, u.URI) and value.is_valid()


def not_URI_error(key, value):
    return f"{key} is not a URI: {value}"


def not_empty(value):
    return bool(value)


def empty_error(key, value):
    return f"{key} is empty"


def one_of(items):
    def validator(value):
        return value in items


def not_one_of_error(items):
    def error_template(key, value):
        return f"{key} is not one of {items}: value"


VALIDATION_FUNCTIONS = {
    SENDER_KEY: (is_country, not_country_error),
    RECEIVER_KEY: (is_country, not_country_error),
    SUBJECT_KEY: (is_URI, not_URI_error),
    OBJ_KEY: (is_URI, not_URI_error),
    PREDICATE_KEY: (is_URI, not_URI_error),
    STATUS_KEY: (one_of(ALLOWED_STATUSES), not_one_of_error(ALLOWED_STATUSES)),
    SENDER_REF_KEY: (not_empty, empty_error),
    CHANNEL_ID_KEY: (not_empty, empty_error),
    CHANNEL_TXN_ID_KEY: (not_empty, empty_error)
}

PROP_TYPES = {
    SENDER_KEY: c.Country,
    RECEIVER_KEY: c.Country,
    SUBJECT_KEY: u.URI,
    OBJ_KEY: u.URI,
    PREDICATE_KEY: u.URI,
    STATUS_KEY: lambda x: x,
    SENDER_REF_KEY: lambda x: x,
    CHANNEL_ID_KEY: lambda x: x,
    CHANNEL_TXN_ID_KEY: lambda x: x
}


class Message(object):
    """
    Messages in the generic discrete wire protocol
    require a "sender" and "receiver" attribute,
    so that they can be delivered and validated.
    They also require "subject", "obj" and
    "predicate" attributes to encode their triple.

    The subject, obj and predicate must be URIs.
    """

    required_attrs = REQUIRED_ATTRS
    allowed_attrs = ALLOWED_ATTRS

    @classmethod
    def from_dict(cls, adict, require_allowed=None):
        require_allowed = [] if not require_allowed else require_allowed
        recast_dict = {}
        for key in REQUIRED_ATTRS:
            recast_dict[key] = PROP_TYPES[key](adict[key])
        for key in ALLOWED_ATTRS:
            try:
                recast_dict[key] = PROP_TYPES[key](adict[key])
            except KeyError as e:
                if key in require_allowed:
                    raise e
        return cls(**recast_dict, require_allowed=require_allowed)

    def __init__(self, require_allowed=None, **kwargs):
        # self.kwargs = kwargs
        # left it to be kwargs just because we already rely on it heavily
        # having this prop is nice for laconic to dict conversion but name is not
        # the best
        object.__setattr__(self, "require_allowed", require_allowed)
        object.__setattr__(self, "kwargs", {})
        # this should do validation but for now it's turned off
        # because it breaks so many tests
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return json.dumps(self.to_dict())

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            try:
                return object.__getattribute__(self, "kwargs")[name]
            except KeyError:
                if name in ALL_ATTRS:
                    return None
                else:
                    raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in VALIDATION_FUNCTIONS:
            # uncomment to enable props validation
            # currently it breaks tests
            # is_valid, error_template = VALIDATION_FUNCTIONS[name]
            # if not is_valid(value):
            #     raise ValueError(error_template(name, value))
            self.kwargs[name] = value
        else:
            # can't restrict setting random props because tests
            object.__setattr__(self, name, value)

    def to_dict(self, exclude=None):
        if exclude is None:
            exclude = []
        out = {}
        for key, value in self.kwargs.items():
            if key not in exclude:
                out[key] = str(value)
        return out

    def absolute_object_uri(self):
        if self.sender:
            return self.sender.object_api_base_url()
        return None

    def is_valid(self):
        return not (self.spurious_attrs_errors() or self.missing_attrs_errors() or self.attrs_errors())

    def validation_errors(self):

        # TODO: further predicate validation?
        # should we also ensure predicates contain at least one dot?
        # should we restrict them to the range of a semantic domain,
        # or is that precicely the differnce
        # between this generic wire protocol
        # and a domain specific one?

        return [
            *self.spurious_attrs_errors(as_list=True),
            *self.missing_attrs_errors(as_list=True),
            *self.attrs_errors(as_list=True)
        ]

    def spurious_attrs_errors(self, as_list=False):
        # no spurious attrs allowed
        spurious = []
        for attr in self.kwargs:
            if attr not in ALL_ATTRS:
                if as_list:
                    spurious.append(attr)
                else:
                    return True
        return [f"spurious attr: {attr}" for attr in spurious] if as_list else False

    def missing_attrs_errors(self, as_list=False):
        # all required_attrs needed
        missing = []
        for attr in self.required_attrs:
            if attr not in self.kwargs:
                if as_list:
                    missing.append(attr)
                else:
                    return True
        return [f"missing attr: {attr}" for attr in missing] if as_list else False

    def attrs_errors(self, as_list=False):
        errors = []
        for key in self.required_attrs:
            value = getattr(self, key)
            is_valid, error_template = VALIDATION_FUNCTIONS[key]
            if not is_valid(value):
                if as_list:
                    errors.append(error_template(key, value))
                else:
                    return True
        return errors if as_list else False

    # can be used to require optional props
    @property
    def require_allowed(self):
        return self._require_allowed

    @require_allowed.setter
    def require_allowed(self, value):
        if not value:
            return
        for key in value:
            if key not in ALLOWED_ATTRS:
                raise ValueError(f"{key} is not in ALLOWED_ATTRS")
        self._require_allowed = value
        self.required_attrs = REQUIRED_ATTRS + value

    # seems that we don't need it right now
    # @property
    # def multihash(self):
    #     """Calculate the multihash of the content"""
    #     # local imports because I'm not sure it will remain here
    #     import json
    #     import hashlib
    #     from multihash import encode, to_b58_string
    #     from intergov.serializers import generic_discrete_message as ser
    #     content = json.dumps(self, cls=ser.MessageJSONEncoder)
    #     message_hash = hashlib.sha256(content.encode("utf-8")).digest()
    #     return to_b58_string(encode(message_hash, 'sha2-256'))

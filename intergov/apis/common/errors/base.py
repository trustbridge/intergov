import re
from http.client import responses as StatusCodeStr


CAMEL_CASE_RE = re.compile('(?:[A-Z][a-z]+)|(?:[A-Z]+)(?=[A-Z][a-z]|$)')

STATUS_ATTR_KEY = 'status'
CODE_ATTR_KEY = 'code'
TITLE_ATTR_KEY = 'title'
DETAIL_ATTR_KEY = 'detail'
SOURCE_ATTR_KEY = 'source'

REQUIRED_ATTRS = [
    STATUS_ATTR_KEY,
    CODE_ATTR_KEY,
    TITLE_ATTR_KEY
]

OPTIONAL_ATTRS = [
    DETAIL_ATTR_KEY,
    SOURCE_ATTR_KEY
]


ALL_ATTRS = REQUIRED_ATTRS + OPTIONAL_ATTRS


def exception_json_template(error_obj):
    # required attrs
    json_dict = {
        # contains string http status(NOT CODE)
        STATUS_ATTR_KEY: getattr(error_obj, STATUS_ATTR_KEY),
        # application specific code? Something like "database-error"
        # can be generated automatically using class name
        CODE_ATTR_KEY: getattr(error_obj, CODE_ATTR_KEY),
        # human readable title, specific to the type of error
        # also can be generated using class name
        TITLE_ATTR_KEY: getattr(error_obj, TITLE_ATTR_KEY),
    }
    # optional attrs
    # this two can only be provided together
    # because detail is human friendly str repr of source, theoretically
    try:
        detail = getattr(error_obj, DETAIL_ATTR_KEY)
        source = getattr(error_obj, SOURCE_ATTR_KEY)
    except AttributeError:
        return json_dict
    # human readable source of the error
    json_dict[DETAIL_ATTR_KEY] = detail
    # machine readable source of the error
    json_dict[SOURCE_ATTR_KEY] = source
    return json_dict


# Usually I name this class UserFriendlyError because it's
# Probably, I overengineered it
# but in the end it's very customizable
class BaseError(Exception):

    ADDITIONAL_KWARGS = []

    def preprocess_kwargs(self, kwargs):

        kwargs = {**kwargs}

        cls = self.__class__

        try:
            kwargs[TITLE_ATTR_KEY]
        except KeyError:
            try:
                kwargs[TITLE_ATTR_KEY] = getattr(cls, TITLE_ATTR_KEY)
            except AttributeError:
                kwargs[TITLE_ATTR_KEY] = cls.camel_case_to_title(cls.__name__)
        try:
            kwargs[CODE_ATTR_KEY]
        except KeyError:
            try:
                kwargs[CODE_ATTR_KEY] = getattr(cls, CODE_ATTR_KEY)
            except AttributeError:
                kwargs[CODE_ATTR_KEY] = cls.camel_case_to_code(cls.__name__)

        # storing orginal value of status to later use it in response
        try:
            self.status_code = kwargs[STATUS_ATTR_KEY]
            kwargs[STATUS_ATTR_KEY] = cls.http_error_code_to_str(kwargs[STATUS_ATTR_KEY])
        except KeyError:
            self.status_code = getattr(cls, STATUS_ATTR_KEY)
            kwargs[STATUS_ATTR_KEY] = cls.http_error_code_to_str(self.status_code)

        return kwargs

    @staticmethod
    def camel_case_to_code(camel_case_code):
        return '-'.join(CAMEL_CASE_RE.findall(camel_case_code)).lower()

    @staticmethod
    def camel_case_to_title(camel_case_title):
        return ' '.join(CAMEL_CASE_RE.findall(camel_case_title))

    @staticmethod
    def http_error_code_to_str(error_code):
        try:
            return StatusCodeStr[error_code]
        except KeyError:
            return str(int(error_code))

    def __init__(
        self,
        *args,
        **kwargs
    ):
        # use these two in property decorators
        # if you want to create them on a fly
        self.args = args
        self.kwargs = kwargs
        kwargs = self.preprocess_kwargs(kwargs)
        for key, value in kwargs.items():
            if key in ALL_ATTRS:
                try:
                    setattr(self, key, value)
                except AttributeError as e:
                    # this way we can use property decorators in exception builders
                    # If you define setter property may be overriden
                    if str(e) != "can't set attribute":
                        raise e
            else:
                if key not in self.ADDITIONAL_KWARGS:
                    raise TypeError('Unexpected keyword argument: {}'.format(key))

    def to_dict(self):
        return exception_json_template(self)


setattr(BaseError, SOURCE_ATTR_KEY, [])

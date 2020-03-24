from http import HTTPStatus


STATUS_PROP_KEY = 'status'
DETAIL_PROP_KEY = 'detail'
SOURCE_PROP_KEY = 'source'
GENERIC_HTTP_ERROR_PROP_KEY = 'generic_http_error'


PROPS = [
    STATUS_PROP_KEY,
    DETAIL_PROP_KEY,
    SOURCE_PROP_KEY,
    GENERIC_HTTP_ERROR_PROP_KEY
]


class UseCaseError(Exception):
    """
    Base class for all use case error
    Its primary purpose is a simplification of an error handling on the
    APIs side. Therefore each UseCaseError can be used as a generic HTTP error.
    If generic_http_error flag is set to False use case will be rendered
    on APIs side as any other custom exception with code=use-case-error
    """
    # render error as generic http error
    generic_http_error = False
    # HTTP status code
    status = HTTPStatus.INTERNAL_SERVER_ERROR
    # human readable error explanation
    detail = ""
    # machine friendly error details
    source = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        kwargs = {**{key: getattr(self, key) for key in PROPS}, **kwargs}
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __setattr__(self, key, value):
        if key == STATUS_PROP_KEY:
            try:
                value = HTTPStatus(value)
            except IndexError:
                raise ValueError(f"{STATUS_PROP_KEY} must be valid HTTP status code, got {value}")
        elif key == DETAIL_PROP_KEY:
            if not isinstance(value, str):
                raise ValueError(f"{DETAIL_PROP_KEY} must be str, got {type(value)}:{value}")
        elif key == SOURCE_PROP_KEY:
            if not isinstance(value, list):
                raise ValueError(f"{SOURCE_PROP_KEY} must be list, got {type(value)}:{value}")
        elif key == GENERIC_HTTP_ERROR_PROP_KEY:
            if not isinstance(value, bool):
                raise ValueError(f"{GENERIC_HTTP_ERROR_PROP_KEY} must be bool, got {type(value)}:{value}")
        object.__setattr__(self, key, value)


#  the most popular error in our use cases for now
class NotFoundError(UseCaseError):
    generic_http_error = True
    status = HTTPStatus.NOT_FOUND


# the second most popular error, pure assumption but I think so
class ConflictError(UseCaseError):
    generic_http_error = True
    status = HTTPStatus.CONFLICT


# should be used as ValueError to show that execution is impossible due
# to incorrect parameters
class BadParametersError(UseCaseError):
    generic_http_error = True
    status = HTTPStatus.BAD_REQUEST

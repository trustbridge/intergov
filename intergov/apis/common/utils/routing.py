import functools
from http import HTTPStatus as StatusCode
from flask import (
    request
)
from intergov.apis.common import errors


def UnsupportedMediaTypeError(got, include, exclude):
    detail = 'Unsupported mimetype. Value: "{}".'.format(got)
    if include:
        detail += ' Value must be one of {}.'.format(include)
    if exclude:
        detail += ' Value must not be one of {}.'.format(exclude)
    source = {
        'value': got,
        'include': include,
        'exclude': exclude
    }
    return errors.GenericHTTPError(
        StatusCode.UNSUPPORTED_MEDIA_TYPE,
        detail=detail,
        source=source
    )


def mimetype(include=[], exclude=[]):
    if not (include or exclude):
        raise ValueError(
            'Can\'t use mimetype request decorator with include=[] and exclude=[]'
        )

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if include:
                if request.mimetype not in include:
                    raise UnsupportedMediaTypeError(request.mimetype, include, exclude)
            if exclude:
                if request.mimetype in exclude:
                    raise UnsupportedMediaTypeError(request.mimetype, include, exclude)
            return func(*args, **kwargs)
        return wrapper
    return decorator

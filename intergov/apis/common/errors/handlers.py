from http import HTTPStatus as StatusCode
from werkzeug.exceptions import HTTPException
from flask import (
    jsonify
)
from intergov.use_cases.common.errors import UseCaseError as CommonUseCaseError
from intergov.loggers import logging  # NOQA
from . import (
    BaseError,
    InternalServerError,
    GenericHTTPError,
    ErrorsList,
    UseCaseError
)


# standard requires response to contain errors array
def error_response_json_template(*errors):
    return {
        'errors': [e.to_dict() for e in errors]
    }


def error_response(*errors):
    resp = jsonify(error_response_json_template(*errors))
    if len(errors) > 1:
        resp.status_code = StatusCode.BAD_REQUEST
    elif len(errors) == 1:
        resp.status_code = errors[0].status_code
    else:
        raise ValueError('Cannot create error response without errors')
    return resp


# handler for multiply exceptions, because standard allows such thing
def handle_custom_exceptions_list(exception):
    return error_response(*exception.errors)


# handler for our custom errors
def handle_custom_exception(error):
    return error_response(error)


# handles all werkzeug.exceptions.HTTPException
def handle_generic_http_exception(error):
    return error_response(GenericHTTPError(error))


# for really bad situations when we can't handle the error at all
def handle_generic_exception(error):
    logging.exception(error)
    return error_response(InternalServerError(error))


# for our nice use cases internal errors which still may be user friendly
def handle_use_case_error(error):
    if error.generic_http_error:
        return error_response(
            GenericHTTPError(
                error.status,
                detail=error.detail,
                source=error.source
            )
        )
    else:
        return error_response(UseCaseError(error))


# just a shortcut
def register(app):
    app.register_error_handler(ErrorsList, handle_custom_exceptions_list)
    app.register_error_handler(BaseError, handle_custom_exception)
    app.register_error_handler(HTTPException, handle_generic_http_exception)
    app.register_error_handler(CommonUseCaseError, handle_use_case_error)
    app.register_error_handler(Exception, handle_generic_exception)

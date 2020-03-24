from http import HTTPStatus as StatusCode
from http.client import responses as StatusCodeStr
import pytest
from werkzeug import exceptions
from intergov.apis.common.errors import (
    BaseError,
    ValidationError,
    InternalServerError,
    GenericHTTPError,
    UseCaseError,
    MissingAttributesError,
    ErrorsList
)

from intergov.apis.common.errors.api import message
from intergov.use_cases.common import errors as use_case_errors
from intergov.apis.common.errors import handlers

STATUS_KEY = 'status'
CODE_KEY = 'code'
TITLE_KEY = 'title'
DETAIL_KEY = 'detail'
SOURCE_KEY = 'source'

CUSTOM_ERROR_KWARGS = {
    STATUS_KEY: StatusCode.INTERNAL_SERVER_ERROR,
    CODE_KEY: 'custom-error',
    TITLE_KEY: 'Custom Error',
    DETAIL_KEY: 'Very custom error, we can\'t handle it',
    SOURCE_KEY: [
        'very-custom-error',
    ]
}

CUSTOM_ERROR_DICT = {
    **CUSTOM_ERROR_KWARGS,
    'status': "Internal Server Error"
}

ERROR_KWARGS = {
    DETAIL_KEY: 'Details',
    SOURCE_KEY: [
        {'bad': 'happened'}
    ]
}


class CustomUseCaseError(use_case_errors.UseCaseError):
    status = StatusCode.BAD_REQUEST
    detail = "Hello my custom error!"
    source = ['Feeling quite ok, but still give you an error!']


# testing the creation of custom error for single use
def test_base_error():
    error = BaseError(**CUSTOM_ERROR_KWARGS)
    assert error.to_dict() == CUSTOM_ERROR_DICT

    strange_status_code = 1000

    kwargs = {
        **CUSTOM_ERROR_KWARGS,
        STATUS_KEY: strange_status_code
    }

    to_dict_strange_code = {
        **CUSTOM_ERROR_DICT,
        STATUS_KEY: str(strange_status_code)
    }

    error = BaseError(**kwargs)
    assert error.to_dict() == to_dict_strange_code

    kwargs = {
        **CUSTOM_ERROR_KWARGS,
        'strange_key': 'something'
    }

    with pytest.raises(TypeError) as e:
        BaseError(**kwargs)

    assert str(e.value) == 'Unexpected keyword argument: strange_key'


# testing the creation of custom error for reuse
def test_base_error_extension():
    # testing generation of the title, code fields
    class CustomError(BaseError):
        status = CUSTOM_ERROR_KWARGS[STATUS_KEY]

    # fully static error
    class CustomStaticError(BaseError):
        status = StatusCode.BAD_REQUEST
        title = 'Custom Title'
        code = 'custom-code'
        detail = 'Custom Details'
        source = ['Custom Source']

    error = CustomError(
        detail=CUSTOM_ERROR_KWARGS[DETAIL_KEY],
        source=CUSTOM_ERROR_KWARGS[SOURCE_KEY]
    )
    assert error.to_dict() == CUSTOM_ERROR_DICT
    # test class error fields
    assert CustomStaticError().to_dict() == {
        DETAIL_KEY: CustomStaticError.detail,
        SOURCE_KEY: CustomStaticError.source,
        STATUS_KEY: StatusCodeStr[CustomStaticError.status],
        TITLE_KEY: CustomStaticError.title,
        CODE_KEY: CustomStaticError.code
    }
    # testing overriding class fields by kwargs
    assert CustomStaticError(**CUSTOM_ERROR_KWARGS).to_dict() == CUSTOM_ERROR_DICT

    # testing unhandled attribute error

    strange_attribute_error = AttributeError('Something')

    class CustomErrorInvalidPropSetter(BaseError):
        @property
        def status(self):
            return "404"

        @status.setter
        def status(self, value):
            raise strange_attribute_error

    with pytest.raises(AttributeError) as e:
        CustomErrorInvalidPropSetter(**CUSTOM_ERROR_KWARGS)

    assert str(e.value) == str(strange_attribute_error)


# testing set of basic predefined error classes
def test_basic_errors():

    assert UseCaseError(CustomUseCaseError()).to_dict() == {
        TITLE_KEY: 'Custom Use Case Error',
        STATUS_KEY: 'Bad Request',
        CODE_KEY: 'use-case-error',
        DETAIL_KEY: CustomUseCaseError.detail,
        SOURCE_KEY: CustomUseCaseError.source
    }

    assert ValidationError(**ERROR_KWARGS).to_dict() == {
        STATUS_KEY: 'Bad Request',
        CODE_KEY: 'validation-error',
        TITLE_KEY: 'Validation Error',
        **ERROR_KWARGS
    }

    assert MissingAttributesError(['1', '2', '3']).to_dict() == {
        TITLE_KEY: 'Missing Attributes Error',
        CODE_KEY: 'missing-attributes-error',
        STATUS_KEY: 'Bad Request',
        DETAIL_KEY: "Missing required attributes: ['1', '2', '3'].",
        SOURCE_KEY: ['1', '2', '3']
    }

    assert InternalServerError(Exception('Test')).to_dict() == {
        STATUS_KEY: 'Internal Server Error',
        CODE_KEY: 'internal-server-error',
        TITLE_KEY: 'Internal Server Error',
        SOURCE_KEY: [
            {
                'type': Exception.__name__,
                'str': str(Exception('Test'))
            }
        ],
        DETAIL_KEY: 'Unexpected server error occured.'
    }

    # testing generation of required fields using werkzeug.exceptions
    # used for error handler generic http excetions formatting
    assert GenericHTTPError(exceptions.MethodNotAllowed()).to_dict() == {
        STATUS_KEY: 'Method Not Allowed',
        CODE_KEY: 'generic-http-error',
        TITLE_KEY: 'Method Not Allowed'
    }

    # testing equality between 3 different creation methods
    assert GenericHTTPError(exceptions.NotFound()).to_dict() == GenericHTTPError(404).to_dict()
    assert GenericHTTPError(exceptions.NotFound()).to_dict() == GenericHTTPError(StatusCode.NOT_FOUND).to_dict()
    # testing exception cases
    with pytest.raises(ValueError) as e:
        GenericHTTPError(0)
        assert str(e) == 'Non generic HTTP exception. Can\'t find class for status: "0"'
    with pytest.raises(TypeError) as e:
        GenericHTTPError("Not Found")
        assert str(e) == (
            'GenericHTTPError "exception" kwarg must be the instance of:'
            + "['werkzeug.exceptions.HTTPException', 'http.HTTPStatus', 'int']"
        )
    # testing extension of standard errors
    not_found_extended_dict = GenericHTTPError(
        exceptions.NotFound(),
        detail='Something',
        source=['Something']
    ).to_dict()

    assert not_found_extended_dict == {
        STATUS_KEY: 'Not Found',
        CODE_KEY: 'generic-http-error',
        TITLE_KEY: 'Not Found',
        DETAIL_KEY: 'Something',
        SOURCE_KEY: ['Something']
    }
    # this way of creation is my favorite
    assert not_found_extended_dict == GenericHTTPError(
        StatusCode.NOT_FOUND,
        detail='Something',
        source=['Something']
    ).to_dict()
    # this one is ok, but it's always better to use constants
    assert not_found_extended_dict == GenericHTTPError(
        404,
        detail='Something',
        source=['Something']
    ).to_dict()

    # using enum item object
    assert not_found_extended_dict == GenericHTTPError(
        StatusCode(404),
        detail='Something',
        source=['Something']
    ).to_dict()

    with pytest.raises(ValueError) as e:
        ErrorsList(Exception('Hello'), GenericHTTPError(404))
    assert str(e.value) == 'All errors should be the instance of BaseError'


def test_common_message_api_errors():
    assert message.MessageDataEmptyError().to_dict() == {
        STATUS_KEY: 'Bad Request',
        CODE_KEY: 'message-data-empty-error',
        TITLE_KEY: 'Message Data Empty Error',
        DETAIL_KEY: 'A single non-empty JSON must be passed',
        SOURCE_KEY: []
    }
    assert message.MessageDeserializationError().to_dict() == {
        STATUS_KEY: 'Bad Request',
        CODE_KEY: 'message-deserialization-error',
        TITLE_KEY: 'Message Deserialization Error',
        DETAIL_KEY: 'Unable to deserialize the posted message',
        SOURCE_KEY: []
    }
    assert message.MessageValidationError().to_dict() == {
        STATUS_KEY: 'Bad Request',
        CODE_KEY: 'message-validation-error',
        TITLE_KEY: 'Message Validation Error',
        DETAIL_KEY: 'Unable to validate the posted message',
        SOURCE_KEY: []
    }
    assert message.MessageAbsoluteURLError().to_dict() == {
        STATUS_KEY: 'Bad Request',
        CODE_KEY: 'message-absolute-url-error',
        TITLE_KEY: 'Message Absolute URL Error',
        DETAIL_KEY: 'Unable to identify absolute URI of message',
        SOURCE_KEY: []
    }
    assert message.UnableWriteToInboxError().to_dict() == {
        STATUS_KEY: 'Internal Server Error',
        CODE_KEY: 'unable-write-to-inbox-error',
        TITLE_KEY: 'Unable Write To Inbox Error',
        DETAIL_KEY: 'Unexpected error, unable write to inbox',
        SOURCE_KEY: []
    }


def test_error_handlers(app, client):

    generic_http_use_case_error_instance = CustomUseCaseError(generic_http_error=True)
    use_case_error_instance = CustomUseCaseError()

    custom_error_instance = ValidationError()
    generic_http_error_instance = exceptions.NotFound()
    internal_server_error_exception_instance = Exception('Error')
    errors_list_instance = ErrorsList(
        custom_error_instance,
        custom_error_instance
    )

    @app.route('/post-method', methods=['POST'])
    def post_method():
        return 'Hello'

    @app.route('/errors-list')
    def errors_list():
        raise errors_list_instance

    @app.route('/generic-http-error')
    def generic_http_error():
        raise generic_http_error_instance

    @app.route('/internal-server-error')
    def internal_server_error():
        raise internal_server_error_exception_instance

    @app.route('/custom-error')
    def custom_error():
        raise custom_error_instance

    @app.route('/use-case-error')
    def use_case_error():
        raise use_case_error_instance

    @app.route('/generic-http-use-case-error')
    def generic_http_use_case_error():
        raise generic_http_use_case_error_instance

    # testing flask defaul error wrapping
    resp = client.get('/post-method')
    assert resp.status_code == StatusCode.METHOD_NOT_ALLOWED, resp.data
    assert resp.get_json() == handlers.error_response_json_template(
        GenericHTTPError(StatusCode.METHOD_NOT_ALLOWED)
    )

    # testing werkzeug error thrown manually
    resp = client.get('/generic-http-error')
    assert resp.status_code == StatusCode.NOT_FOUND, resp.data
    assert resp.get_json() == handlers.error_response_json_template(
        GenericHTTPError(generic_http_error_instance)
    )

    # testing internal exception error
    resp = client.get('/internal-server-error')
    assert resp.status_code == StatusCode.INTERNAL_SERVER_ERROR, resp.data
    assert resp.get_json() == handlers.error_response_json_template(
        InternalServerError(internal_server_error_exception_instance)
    )

    # testing custom error
    resp = client.get('/custom-error')
    assert resp.status_code == custom_error_instance.status_code, resp.data
    assert resp.get_json() == handlers.error_response_json_template(
        custom_error_instance
    )

    # testing several errors response
    resp = client.get('/errors-list')
    assert resp.status_code == StatusCode.BAD_REQUEST, resp.data
    assert resp.get_json() == handlers.error_response_json_template(
        *errors_list_instance.errors
    )

    # testing use case error
    resp = client.get('/use-case-error')
    assert resp.status_code == use_case_error_instance.status, resp.data
    assert resp.get_json() == handlers.error_response_json_template(
        UseCaseError(use_case_error_instance)
    )

    # testing use case
    resp = client.get('/generic-http-use-case-error')
    assert resp.status_code == generic_http_use_case_error_instance.status, resp.data
    assert resp.get_json() == handlers.error_response_json_template(
        GenericHTTPError(
            generic_http_use_case_error_instance.status,
            detail=generic_http_use_case_error_instance.detail,
            source=generic_http_use_case_error_instance.source
        )
    )

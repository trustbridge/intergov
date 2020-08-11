import json
import io
from http import HTTPStatus
from unittest import mock
from intergov.domain.jurisdiction import Jurisdiction
from tests.unit.apis.common.auth.test import VALID_AUTH_NO_ROLE_JSON, _create_auth_headers

from tests.unit.domain.wire_protocols.test_generic_message import (
    _random_multihash
)

from intergov.apis.common.utils.routing import (
    UnsupportedMediaTypeError
)

from intergov.apis.common.errors import (
    InternalServerError
)

from intergov.apis.common.errors.handlers import (
    error_response_json_template
)

from intergov.apis.document.exceptions import (
    TooManyFilesError,
    NoInputFileError,
    BadJurisdictionNameError,
    DocumentNotFoundError,
    InvalidURIError
)

VALID_JURISDICTION_NAME = 'US'
INVALID_JURISDICTION_NAME = 'USUS'

VALID_JURISDICTION_AUTH_JSON = {**VALID_AUTH_NO_ROLE_JSON, 'jurisdiction': VALID_JURISDICTION_NAME}
INVALID_JURISDICTION_AUTH_JSON = {**VALID_AUTH_NO_ROLE_JSON, 'jurisdiction': INVALID_JURISDICTION_NAME}

VALID_AUTH_HEADERS = _create_auth_headers(VALID_JURISDICTION_AUTH_JSON)
INVALID_AUTH_HEADERS = _create_auth_headers(INVALID_JURISDICTION_AUTH_JSON)

DOCUMENT_POST_URL = '/jurisdictions/{}'
DOCUMENT_GET_URL = '/{}'
VALID_DOCUMENT_URI = _random_multihash()
INVALID_DOCUMENT_URI = _random_multihash() + "not multihash"

OBJECT_LAKE_REPO_CLASS = 'intergov.apis.document.documents.ObjectLakeRepo'
OBJECT_ACL_REPO_CLASS = 'intergov.apis.document.documents.ObjectACLRepo'
AUTHENTICATED_OBJECT_ACCESS_USE_CASE_CLASS = 'intergov.apis.document.documents.AuthenticatedObjectAccessUseCase'
RECORD_OBJECT_USE_CASE_CLASS = 'intergov.apis.document.documents.RecordObjectUseCase'


VALID_POST_REQUEST_JURISDICTION_URL = DOCUMENT_POST_URL.format(VALID_JURISDICTION_NAME)
INVALID_POST_REQUEST_JURISDICTION_URL = DOCUMENT_POST_URL.format(INVALID_JURISDICTION_NAME)

VALID_POST_REQUEST_MIMETYPE = 'multipart/form-data'
INVALID_POST_REQUEST_MIMETYPE = 'application/json'
VALID_POST_RESPONSE_MIMETYPE = 'application/json'
VALID_ERROR_RESPONSE_MIMETYPE = 'application/json'
VALID_GET_RESPONSE_MIMETYPE = 'binary/octet-stream'

DOCUMENT_JSON = {
    'user': {
        'id': 1,
        'name': {
            'first': 'First',
            'last': 'Last'
        },
        'age': 29,
        'sex': 'male'
    },
    'document': {
        'id': None,
        'content': 'Test content'
    }
}


DOCUMENT_MULTIHASH_KEY = 'multihash'


# must create new ones because streams will be closed after requests sent
def get_valid_post_request_files():
    return {
        'one': (io.BytesIO(json.dumps(DOCUMENT_JSON).encode()), 'document.json')
    }


def get_too_many_post_request_files():
    return {
        'one': (io.BytesIO(json.dumps(DOCUMENT_JSON).encode()), 'document.json'),
        'two': (io.BytesIO(json.dumps(DOCUMENT_JSON).encode()), 'document.json')
    }


def test_errors(client):

    assert InvalidURIError().to_dict() == {
        'status': 'Bad Request',
        'title': 'Invalid URI Error',
        'code': 'invalid-uri-error',
        'detail': 'URI is not multihash',
        'source': []
    }

    assert BadJurisdictionNameError(Exception('hey')).to_dict() == {
        'status': 'Bad Request',
        'title': 'Bad Jurisdiction Name Error',
        'code': 'bad-jurisdiction-name-error',
        'detail': 'Received invalid/unknown jurisdiction name',
        'source': [
            str(Exception('hey'))
        ]
    }
    assert NoInputFileError().to_dict() == {
        'status': 'Bad Request',
        'code': 'no-input-file-error',
        'title': 'No Input File Error',
        'detail': 'Received no input file',
        'source': []
    }
    assert TooManyFilesError(10).to_dict() == {
        'status': 'Bad Request',
        'code': 'too-many-files-error',
        'title': 'Too Many Files Error',
        'detail': 'Too many files. Only one file must be provided.',
        'source': [
            {
                'files': 10
            }
        ]
    }
    assert DocumentNotFoundError('a', 'b').to_dict() == {
        'status': 'Not Found',
        'code': 'generic-http-error',
        'title': 'Not Found',
        'detail': 'Document with uri:a for jurisdiction:b not found',
        'source': [
            {
                'uri': 'a',
                'jurisdiction': 'b'
            }
        ]
    }


@mock.patch(OBJECT_ACL_REPO_CLASS)
@mock.patch(OBJECT_LAKE_REPO_CLASS)
def test_post_document(ObjectLakeRepoMock, ObjectACLRepoMock, client):

    allow_access_to = ObjectACLRepoMock.return_value.allow_access_to
    post_from_file_obj = ObjectLakeRepoMock.return_value.post_from_file_obj

    resp = client.post(
        VALID_POST_REQUEST_JURISDICTION_URL,
        mimetype=VALID_POST_REQUEST_MIMETYPE,
        data=get_valid_post_request_files()
    )

    assert resp.status_code == HTTPStatus.OK, resp.body
    assert resp.mimetype == VALID_POST_RESPONSE_MIMETYPE
    assert DOCUMENT_MULTIHASH_KEY in resp.get_json()

    allow_access_to.assert_called_once()
    post_from_file_obj.assert_called_once()


@mock.patch(OBJECT_ACL_REPO_CLASS)
@mock.patch(OBJECT_LAKE_REPO_CLASS)
def test_post_document_errors(ObjectLakeRepoMock, ObjectACLRepoMock, client):

    resp = client.post(
        INVALID_POST_REQUEST_JURISDICTION_URL,
        mimetype=INVALID_POST_REQUEST_MIMETYPE,
        data={}
    )

    assert resp.mimetype == VALID_ERROR_RESPONSE_MIMETYPE
    assert resp.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    assert resp.get_json() == error_response_json_template(
        UnsupportedMediaTypeError(
            INVALID_POST_REQUEST_MIMETYPE,
            [VALID_POST_REQUEST_MIMETYPE],
            []
        )
    )

    try:
        Jurisdiction(INVALID_JURISDICTION_NAME)
    except Exception as e:
        jurisdiction_exception = e

    resp = client.post(
        INVALID_POST_REQUEST_JURISDICTION_URL,
        mimetype=VALID_POST_REQUEST_MIMETYPE,
        data={}
    )

    assert resp.mimetype == VALID_ERROR_RESPONSE_MIMETYPE
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.get_json() == error_response_json_template(
        BadJurisdictionNameError(jurisdiction_exception)
    )

    resp = client.post(
        VALID_POST_REQUEST_JURISDICTION_URL,
        mimetype=VALID_POST_REQUEST_MIMETYPE,
        data={}
    )

    assert resp.mimetype == VALID_ERROR_RESPONSE_MIMETYPE
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.get_json() == error_response_json_template(
        NoInputFileError()
    )

    resp = client.post(
        VALID_POST_REQUEST_JURISDICTION_URL,
        mimetype=VALID_POST_REQUEST_MIMETYPE,
        data=get_too_many_post_request_files()
    )

    assert resp.mimetype == VALID_ERROR_RESPONSE_MIMETYPE
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.get_json() == error_response_json_template(
        TooManyFilesError(2)
    )

    allow_access_to = ObjectACLRepoMock.return_value.allow_access_to
    post_from_file_obj = ObjectLakeRepoMock.return_value.post_from_file_obj

    allow_access_to.side_effect = Exception('Very bad thing: ACL')
    post_from_file_obj.side_effect = Exception('Very bad thing: Lake')

    resp = client.post(
        VALID_POST_REQUEST_JURISDICTION_URL,
        mimetype=VALID_POST_REQUEST_MIMETYPE,
        data=get_valid_post_request_files()
    )

    allow_access_to.assert_called_once()

    assert resp.mimetype == VALID_ERROR_RESPONSE_MIMETYPE
    assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert resp.get_json() == error_response_json_template(
        InternalServerError(allow_access_to.side_effect)
    )

    allow_access_to.reset_mock()
    allow_access_to.side_effect = None

    resp = client.post(
        VALID_POST_REQUEST_JURISDICTION_URL,
        mimetype=VALID_POST_REQUEST_MIMETYPE,
        data=get_valid_post_request_files()
    )

    allow_access_to.assert_called_once()
    post_from_file_obj.assert_called_once()

    assert resp.mimetype == VALID_ERROR_RESPONSE_MIMETYPE
    assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert resp.get_json() == error_response_json_template(
        InternalServerError(post_from_file_obj.side_effect)
    )


@mock.patch(OBJECT_ACL_REPO_CLASS)
@mock.patch(OBJECT_LAKE_REPO_CLASS)
def test_get_document(ObjectLakeRepoMock, ObjectACLRepoMock, client):

    # testing jurisdiction behaviour
    search = ObjectACLRepoMock.return_value.search
    search.return_value = [Jurisdiction(VALID_JURISDICTION_NAME)]

    get_body = ObjectLakeRepoMock.return_value.get_body
    get_body.return_value = json.dumps(DOCUMENT_JSON)

    resp = client.get(
        DOCUMENT_GET_URL.format(VALID_DOCUMENT_URI),
        headers=VALID_AUTH_HEADERS
    )

    assert resp.mimetype == VALID_GET_RESPONSE_MIMETYPE, resp.data
    assert resp.status_code == HTTPStatus.OK, resp.data
    assert json.loads(resp.data) == DOCUMENT_JSON, resp.data

    search.assert_called_once()
    get_body.assert_called_once()


@mock.patch(OBJECT_ACL_REPO_CLASS)
@mock.patch(OBJECT_LAKE_REPO_CLASS)
def test_get_document_errors(ObjectLakeRepoMock, ObjectACLRepoMock, client):

    # # testing unauthorized
    # resp = client.get(DOCUMENT_GET_URL.format(VALID_DOCUMENT_URI))
    # assert resp.status_code == HTTPStatus.UNAUTHORIZED

    # testing invalid URI error
    resp = client.get(
        DOCUMENT_GET_URL.format(INVALID_DOCUMENT_URI),
        headers=VALID_AUTH_HEADERS
    )

    assert resp.mimetype == VALID_ERROR_RESPONSE_MIMETYPE, resp.data
    assert resp.status_code == HTTPStatus.BAD_REQUEST, resp.data
    assert resp.get_json() == error_response_json_template(
        InvalidURIError()
    )

    # testing invalid jurisdiction auth headers
    try:
        Jurisdiction(INVALID_JURISDICTION_NAME)
    except Exception as e:
        jurisdiction_exception = e

    resp = client.get(
        DOCUMENT_GET_URL.format(VALID_DOCUMENT_URI),
        headers=INVALID_AUTH_HEADERS
    )

    assert resp.mimetype == VALID_ERROR_RESPONSE_MIMETYPE, resp.data
    assert resp.status_code == HTTPStatus.BAD_REQUEST, resp.data
    assert resp.get_json() == error_response_json_template(
        BadJurisdictionNameError(jurisdiction_exception)
    )

    search = ObjectACLRepoMock.return_value.search
    get_body = ObjectLakeRepoMock.return_value.get_body

    # testing not authenticated user
    search.return_value = []

    resp = client.get(
        DOCUMENT_GET_URL.format(VALID_DOCUMENT_URI),
        headers=VALID_AUTH_HEADERS
    )

    search.assert_called_once()
    get_body.assert_not_called()

    assert resp.mimetype == VALID_ERROR_RESPONSE_MIMETYPE, resp.data
    assert resp.status_code == HTTPStatus.NOT_FOUND, resp.data
    assert resp.get_json() == error_response_json_template(
        DocumentNotFoundError(
            VALID_DOCUMENT_URI,
            Jurisdiction(VALID_JURISDICTION_NAME)
        )
    )

    # testing unexpected acl repo error
    search.reset_mock()
    get_body.reset_mock()
    search.side_effect = Exception('Very bad times indeed')

    resp = client.get(
        DOCUMENT_GET_URL.format(VALID_DOCUMENT_URI),
        headers=VALID_AUTH_HEADERS
    )

    search.assert_called_once()
    get_body.assert_not_called()

    assert resp.mimetype == VALID_ERROR_RESPONSE_MIMETYPE, resp.data
    assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR, resp.data
    assert resp.get_json() == error_response_json_template(
        InternalServerError(search.side_effect)
    )

    # testing expected lake repo error
    class NoSuchKey(Exception):
        pass

    search.reset_mock()
    get_body.reset_mock()
    search.side_effect = None
    search.return_value = [Jurisdiction(VALID_JURISDICTION_NAME)]
    get_body.side_effect = NoSuchKey

    resp = client.get(
        DOCUMENT_GET_URL.format(VALID_DOCUMENT_URI),
        headers=VALID_AUTH_HEADERS
    )

    search.assert_called_once()
    get_body.assert_called_once()

    assert resp.mimetype == VALID_ERROR_RESPONSE_MIMETYPE, resp.data
    assert resp.status_code == HTTPStatus.NOT_FOUND, resp.data
    assert resp.get_json() == error_response_json_template(
        DocumentNotFoundError(
            VALID_DOCUMENT_URI,
            Jurisdiction(VALID_JURISDICTION_NAME)
        )
    )

    # testing get_body return None
    # Can it even happen? Or we should consider NoSuchKey
    # error to be only way to get None as a result
    # of the use case?

    search.reset_mock()
    get_body.reset_mock()
    search.return_value = [Jurisdiction(VALID_JURISDICTION_NAME)]
    get_body.side_effect = None
    get_body.return_value = None

    resp = client.get(
        DOCUMENT_GET_URL.format(VALID_DOCUMENT_URI),
        headers=VALID_AUTH_HEADERS
    )

    search.assert_called_once()
    get_body.assert_called_once()

    assert resp.mimetype == VALID_ERROR_RESPONSE_MIMETYPE, resp.data
    assert resp.status_code == HTTPStatus.NOT_FOUND, resp.data
    assert resp.get_json() == error_response_json_template(
        DocumentNotFoundError(
            VALID_DOCUMENT_URI,
            Jurisdiction(VALID_JURISDICTION_NAME)
        )
    )

    # testing unexpected lake repo error
    search.reset_mock()
    get_body.reset_mock()
    search.return_value = [Jurisdiction(VALID_JURISDICTION_NAME)]
    get_body.side_effect = Exception('Bad times came')

    resp = client.get(
        DOCUMENT_GET_URL.format(VALID_DOCUMENT_URI),
        headers=VALID_AUTH_HEADERS
    )

    search.assert_called_once()
    get_body.assert_called_once()

    assert resp.mimetype == VALID_ERROR_RESPONSE_MIMETYPE, resp.data
    assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR, resp.data
    assert resp.get_json() == error_response_json_template(
        InternalServerError(get_body.side_effect)
    )

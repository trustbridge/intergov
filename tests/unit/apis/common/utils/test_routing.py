from http import HTTPStatus as StatusCode
import pytest
from intergov.apis.common.utils import routing
from intergov.apis.common.errors import handlers


def test_errors():
    got = 'e'
    include = ['a', 'b']
    exclude = ['c', 'd']
    assert routing.UnsupportedMediaTypeError(got, include, exclude).to_dict() == {
        'title': 'Unsupported Media Type',
        'status': 'Unsupported Media Type',
        'code': 'generic-http-error',
        'detail': (
            'Unsupported mimetype. Value: "{}".'.format(got)
            + ' Value must be one of {}.'.format(include)
            + ' Value must not be one of {}.'.format(exclude)
        ),
        'source': {
            'value': got,
            'include': include,
            'exclude': exclude
        }
    }

    assert routing.UnsupportedMediaTypeError(got, include, []).to_dict() == {
        'title': 'Unsupported Media Type',
        'status': 'Unsupported Media Type',
        'code': 'generic-http-error',
        'detail': (
            'Unsupported mimetype. Value: "{}".'.format(got)
            + ' Value must be one of {}.'.format(include)
            # + ' Value must not be one of {}.'.format(exclude)
        ),
        'source': {
            'value': got,
            'include': include,
            'exclude': []
        }
    }

    assert routing.UnsupportedMediaTypeError(got, [], exclude).to_dict() == {
        'title': 'Unsupported Media Type',
        'status': 'Unsupported Media Type',
        'code': 'generic-http-error',
        'detail': (
            'Unsupported mimetype. Value: "{}".'.format(got)
            # + ' Value must be one of {}.'.format(include)
            + ' Value must not be one of {}.'.format(exclude)
        ),
        'source': {
            'value': got,
            'include': [],
            'exclude': exclude
        }
    }


def test_decorators_errors():
    with pytest.raises(ValueError) as e:
        @routing.mimetype()
        def route():
            pass
    assert str(e.value) == 'Can\'t use mimetype request decorator with include=[] and exclude=[]'


def test_decorators(app, client):

    content_type = 'application/json'
    invalid_content_type = 'text/javascript'

    @app.route('/include')
    @routing.mimetype(['application/json'])
    def mimetype_include_test():
        return 'Hello', StatusCode.OK

    @app.route('/exclude')
    @routing.mimetype([], [invalid_content_type])
    def mimetype_exclude_test():
        return 'Hello', StatusCode.OK

    resp = client.get('/include', content_type=content_type)
    assert resp.status_code == StatusCode.OK, resp.data

    resp = client.get('/include', content_type=invalid_content_type)
    assert resp.status_code == StatusCode.UNSUPPORTED_MEDIA_TYPE, resp.data
    assert resp.get_json() == handlers.error_response_json_template(
        routing.UnsupportedMediaTypeError(
            invalid_content_type,
            [content_type],
            []
        )
    )

    resp = client.get('/exclude', content_type=content_type)
    assert resp.status_code == StatusCode.OK, resp.data

    resp = client.get('/exclude', content_type=invalid_content_type)
    assert resp.status_code == StatusCode.UNSUPPORTED_MEDIA_TYPE, resp.data
    assert resp.get_json() == handlers.error_response_json_template(
            routing.UnsupportedMediaTypeError(
                invalid_content_type,
                [],
                [invalid_content_type]
            )
    )

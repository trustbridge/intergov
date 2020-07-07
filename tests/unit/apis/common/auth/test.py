import json
from http import HTTPStatus

from flask import Response
from intergov.apis.common import demoauth


ROLE_USER = 'user'
ROLE_ADMIN = 'admin'

VALID_AUTH_USER_JSON = {
    'id': 1,
    'role': ROLE_USER
}

VALID_AUTH_ADMIN_JSON = {
    'id': 2,
    'role': ROLE_ADMIN
}

VALID_AUTH_NO_ROLE_JSON = {
    'id': 3
}

JWT_PREFIX = 'JWTBODY'


def _create_auth_headers(data):
    return {
        'Authorization': f'{JWT_PREFIX}{json.dumps(data)}'
    }


def test(app, client):

    @app.route('/authenticated-role-user')
    @demoauth.demo_auth(ROLE_USER, ROLE_ADMIN)
    def authenticated_role_user():
        return Response("Hello", status=HTTPStatus.OK)

    @app.route('/authenticated-role-admin')
    @demoauth.demo_auth(ROLE_ADMIN)
    def authenticated_role_admin():
        return Response("Hello", status=HTTPStatus.OK)

    @app.route('/authenticated-no-role')
    @demoauth.demo_auth()
    def authenticated_no_role():
        return Response("Hello", status=HTTPStatus.OK)

    # test successful auth
    resp = client.get(
        '/authenticated-role-user',
        headers=_create_auth_headers(VALID_AUTH_USER_JSON)
    )
    assert resp.status_code == HTTPStatus.OK

    # testing anyone can access endpoint when role not required
    for auth in [VALID_AUTH_USER_JSON, VALID_AUTH_ADMIN_JSON, VALID_AUTH_NO_ROLE_JSON]:
        resp = client.get(
            '/authenticated-no-role',
            headers=_create_auth_headers(auth)
        )
        assert resp.status_code == HTTPStatus.OK

    # we don't test for invalid values because demo auth became non-restrictive
    # and just does nothing, not attaching the .auth to the request,
    # allowing view to handle that.

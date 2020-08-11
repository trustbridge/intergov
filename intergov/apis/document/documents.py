import json
from http import HTTPStatus

from flask import (
    Blueprint, Response, request,
)

from intergov.domain.jurisdiction import Jurisdiction
from intergov.domain.uri import URI
from intergov.apis.common.errors import (
    InternalServerError
)
from intergov.apis.common.demoauth import demo_auth
from intergov.apis.common.utils import routing
from intergov.loggers import logging  # NOQA
from intergov.monitoring import statsd_timer
from intergov.repos.object_lake import ObjectLakeRepo
from intergov.repos.object_acl import ObjectACLRepo
from intergov.use_cases import (
    AuthenticatedObjectAccessUseCase,
    StoreObjectUseCase
)

from .conf import Config
from .exceptions import (
    TooManyFilesError,
    NoInputFileError,
    BadJurisdictionNameError,
    InvalidURIError,
    DocumentNotFoundError
)

logger = logging.getLogger(__name__)

blueprint = Blueprint('documents', __name__)


@blueprint.route('/jurisdictions/<jurisdiction_name>', methods=['POST'])
@routing.mimetype(['multipart/form-data'])
@statsd_timer("api.document.endpoint.document_post")
def document_post(jurisdiction_name):
    try:
        target_jurisdiction = Jurisdiction(jurisdiction_name)
    except Exception as e:
        raise BadJurisdictionNameError(e)

    object_lake_repo = ObjectLakeRepo(Config.OBJECT_LAKE_CONN)
    object_acl_repo = ObjectACLRepo(Config.OBJECT_ACL_CONN)

    if len(request.files) == 0:
        raise NoInputFileError()
    elif len(request.files) > 1:
        raise TooManyFilesError(len(request.files))

    # get the first file, whatever way it's called
    file = request.files[list(request.files.keys())[0]]

    use_case = StoreObjectUseCase(
        object_acl_repo=object_acl_repo,
        object_lake_repo=object_lake_repo,
    )

    try:
        multihash = use_case.execute(fobj=file, target_jurisdiction=target_jurisdiction)
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(e)

    return Response(
        json.dumps({
            "multihash": multihash,
        }),
        mimetype='application/json',
        status=HTTPStatus.OK
    )


@blueprint.route('/<uri>', methods=['GET'])
@demo_auth()
@statsd_timer("api.document.endpoint.document_fetch")
def document_fetch(uri):
    if not URI(uri).is_valid_multihash():
        raise InvalidURIError()

    object_lake_repo = ObjectLakeRepo(Config.OBJECT_LAKE_CONN)
    object_acl_repo = ObjectACLRepo(Config.OBJECT_ACL_CONN)

    use_case = AuthenticatedObjectAccessUseCase(
        object_acl_repo=object_acl_repo,
        object_lake_repo=object_lake_repo,
    )

    request_auth = getattr(request, "auth", None)
    if request_auth and 'jurisdiction' in request_auth:
        try:
            auth_jurisdiction = Jurisdiction(request_auth['jurisdiction'])
        except Exception as e:
            raise BadJurisdictionNameError(e)
    else:
        # no auth is provided, trust the GET request
        # assuming JWT will handle it
        # TODO: ensure that the auth provided allows access from that country
        try:
            auth_jurisdiction = Jurisdiction(request.args["as_jurisdiction"])
        except Exception as e:
            raise BadJurisdictionNameError(e)

    try:
        document_body = use_case.execute(uri, auth_jurisdiction)
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(e)

    if document_body is not None:
        return Response(
            document_body,
            status=HTTPStatus.OK,
            mimetype='binary/octet-stream',  # TODO: correct mimetype?
            # TODO: some information about the file content?
        )
    else:
        raise DocumentNotFoundError(uri, auth_jurisdiction)

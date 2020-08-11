import json
import uuid
from http import HTTPStatus

from flask import Blueprint, Response, request
from marshmallow import Schema, fields

from intergov.conf import env
from intergov.repos.message_lake import MessageLakeRepo
from intergov.repos.bc_inbox.elasticmq.elasticmqrepo import BCInboxRepo
from intergov.repos.notifications import NotificationsRepo
from intergov.domain.wire_protocols.generic_discrete import (
    Message,
    FINAL_STATUSES,
    STATUS_KEY
)
from intergov.loggers import logging  # NOQA
from intergov.monitoring import statsd_timer
from intergov.serializers import generic_discrete_message as ser
from intergov.use_cases import (
    GetMessageBySenderRefUseCase, EnqueueMessageUseCase,
    PatchMessageMetadataUseCase,
)
from intergov.use_cases.common.errors import (
    UseCaseError
)
from intergov.apis.common.utils import routing
from intergov.apis.common.errors import (
    InternalServerError
)
from intergov.apis.common.errors.api.message import (
    MessageDataEmptyError,
    MessageDeserializationError,
    MessageValidationError,
    UnableWriteToInboxError
)

from .conf import Config
from .exceptions import (
    MessageNotFoundError,
    UnexpectedMessageStatusError
)

blueprint = Blueprint('messages', __name__)
logger = logging.getLogger(__name__)
IGL_JURISDICTION = env('IGL_JURISDICTION', default=None)


class MessageSchema(Schema):
    sender = fields.String(required=True)
    receiver = fields.String(required=True)
    subject = fields.String(required=True)
    obj = fields.String(required=True)
    predicate = fields.String(required=True)
    channel_id = fields.String()
    channel_txn_id = fields.String()
    status = fields.String()
    sender_ref = fields.String()


@statsd_timer("api.message.endpoint.message_retrieve")
@blueprint.route('/message/<reference>', methods=['GET'])
def message_retrieve(reference):
    """
    ---
    get:
      parameters:
      - in: path
        name: reference
        schema:
          type: string
        required: true
      responses:
        201:
          description: Is this the right code?
          content:
            application/json:
              schema: MessageSchema

    """
    # TODO: auth
    repo = MessageLakeRepo(Config.MESSAGE_LAKE_CONN)

    use_case = GetMessageBySenderRefUseCase(repo)

    try:
        message = use_case.execute(reference)
    except Exception as e:
        if e.__class__.__name__ == 'NoSuchKey':
            message = None
        else:
            # logging.exception(e)
            # we have a handler to catch this exception
            # but in future it will be easier to decide
            # what kind of info we want to put here
            raise InternalServerError(e)

    if message:
        return Response(
            json.dumps(message, cls=ser.MessageJSONEncoder),
            status=HTTPStatus.CREATED,
            mimetype='application/json',
            # headers={'Location': message_url}
        )
    else:
        raise MessageNotFoundError(reference)


@statsd_timer("api.message.endpoint.message_patch")
@blueprint.route('/message/<reference>', methods=['PATCH'])
@routing.mimetype(['application/json'])
def message_patch(reference):
    """
    ---
    patch:
      parameters:
      - in: path
        name: reference
        schema:
          type: string
        required: true
      requestBody:
        content:
          application/json:
            schema: MessageSchema
      responses:
        200:
          description: Update a message
          content:
            application/json:
              schema: MessageSchema

    """
    # TODO: auth
    json_payload = request.get_json(silent=True)
    if not json_payload or not isinstance(json_payload, dict):
        raise MessageDataEmptyError()

    status = json_payload.get(STATUS_KEY)

    if status and status not in FINAL_STATUSES:
        raise UnexpectedMessageStatusError(
            json_payload.get('status'),
            FINAL_STATUSES + [None]
        )

    repo = MessageLakeRepo(Config.MESSAGE_LAKE_CONN)
    publish_notifications_repo = NotificationsRepo(
        Config.PUBLISH_NOTIFICATIONS_REPO_CONN
    )

    use_case = PatchMessageMetadataUseCase(
        repo,
        publish_notifications_repo
    )
    try:
        message = use_case.execute(reference, json_payload)
    except UseCaseError as e:
        raise e
    except Exception as e:
        if e.__class__.__name__ == 'NoSuchKey':
            message = None
        else:
            # logging.exception(e)
            # we have a handler to catch this exception
            # but in future it will be easier to decide
            # what kind of info we want to put here
            raise InternalServerError(e)
    if not message:
        raise MessageNotFoundError(reference)
    return Response(
        json.dumps(message, cls=ser.MessageJSONEncoder),
        status=HTTPStatus.OK,
        mimetype='application/json',
    )


@statsd_timer("api.message.endpoint.message_post")
@blueprint.route('/message', methods=['POST'])
@routing.mimetype(['application/json'])
def message_post():
    """
    Puts message to the message lake and into the processing queue
    ---
    post:
      requestBody:
        content:
          application/binary:
            schema: MessageSchema
      responses:
        200:
          description: The message was successfully sent to the node
          content:
            application/json:
              schema: MessageSchema
    """
    body = request.get_json(silent=True)
    if not body or not isinstance(body, dict):
        raise MessageDataEmptyError()

    try:
        message = Message.from_dict(body)
    except Exception as e:
        raise MessageDeserializationError(source=[str(e)])
    if not message.is_valid():
        raise MessageValidationError(source=message.validation_errors())

    # we fill it for message_api but not for message_rx_api
    if not message.sender_ref:
        message.kwargs["sender_ref"] = str(uuid.uuid4())

    if str(IGL_JURISDICTION) == str(message.sender):
        # because we are first who see that message
        message.kwargs["status"] = "pending"
    else:
        message.kwargs["status"] = "received"

    repo = BCInboxRepo(
        Config.BC_INBOX_CONF
    )
    use_case = EnqueueMessageUseCase(repo)

    if use_case.execute(message):
        return Response(
            json.dumps(message, cls=ser.MessageJSONEncoder),
            status=HTTPStatus.CREATED,
            mimetype='application/json',
            # headers={'Location': message_url}
        )
    else:
        raise UnableWriteToInboxError()

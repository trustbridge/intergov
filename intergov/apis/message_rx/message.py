import json
from flask import (
    Blueprint, Response, request
)


from intergov.repos.bc_inbox.elasticmq.elasticmqrepo import BCInboxRepo
from intergov.domain.wire_protocols.generic_discrete import Message
from intergov.monitoring import statsd_timer
from intergov.serializers import generic_discrete_message as ser
from intergov.use_cases import EnqueueMessageUseCase
from intergov.loggers import logging

from intergov.apis.message_rx.conf import Config
from intergov.apis.common.utils import routing
from intergov.apis.common.errors.api.message import (
    MessageDataEmptyError,
    MessageDeserializationError,
    MessageValidationError,
    MessageAbsoluteURLError,
    UnableWriteToInboxError
)


blueprint = Blueprint('message', __name__)
logger = logging.getLogger(__name__)


# this one is probably to be disabled very soon
@statsd_timer("api.message_rx.endpoint.message")
@blueprint.route('/messages', methods=['POST'])
@routing.mimetype(['application/json'])
def message():
    """
    Usage:
        curl -XPOST http://127.0.0.1:5000/messages \
            -H 'Content-type: application/json' \
            -d '{"adf": "ee"}'
    """
    # silent prevents default error which is BadRequest
    body = request.get_json(silent=True)
    if not body or not isinstance(body, dict):
        raise MessageDataEmptyError()

    try:
        message = Message.from_dict(body, require_allowed=["sender_ref"])
    except Exception as e:
        raise MessageDeserializationError(source=[str(e)])
    if not message.is_valid():
        raise MessageValidationError(source=message.validation_errors())

    message_url = message.absolute_object_uri()
    if not message_url:
        raise MessageAbsoluteURLError()

    message.kwargs["status"] = "received"  # because it's RX api

    repo = BCInboxRepo(
        Config.BC_INBOX_CONF
    )

    use_case = EnqueueMessageUseCase(repo)

    if use_case.execute(message):
        return Response(
            json.dumps(message, cls=ser.MessageJSONEncoder),
            status=201,
            mimetype='application/json',
            headers={'Location': message_url}
        )
    else:
        raise UnableWriteToInboxError()


@statsd_timer("api.message_rx.endpoint.channel_message_confirm")
@blueprint.route('/channel-message', methods=['GET'])
# @routing.mimetype(['application/x-www-form-urlencoded'])
def channel_message_confirm():
    """
    Handles subscription verification requests
    https://www.w3.org/TR/websub/#hub-verifies-intent
    hub.mode=subscribe&hub.topic=jurisdiction.AU&
    hub.challenge=e35ad43c-7149-45cb-a8eb-3a5a76a368de&
    hub.lease_seconds=432000
    """
    # TODO: validate topic and mode
    # TODO: validate signature header
    return Response(request.args.get('hub.challenge'))


@statsd_timer("api.message_rx.endpoint.channel_message_receive")
@blueprint.route('/channel-message/<channel_id>', methods=['POST'])
@routing.mimetype(['application/json'])
def channel_message_receive(channel_id):
    """
    Handles the pings
    """
    body = request.get_json(silent=True)
    new_ch_message_id = body["id"]
    # TODO: retrieve that message from the channel worker
    # (using JWT auth we have)
    logger.warning(
        "Got notification about channel message %s but not processing it yet, channel_id: %s",
        new_ch_message_id, channel_id
    )
    return Response()

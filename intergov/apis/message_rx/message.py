import json
from flask import (
    Blueprint, Response, request
)


from intergov.repos.bc_inbox.elasticmq.elasticmqrepo import BCInboxRepo
from intergov.domain.wire_protocols.generic_discrete import Message
from intergov.monitoring import statsd_timer
from intergov.serializers import generic_discrete_message as ser
from intergov.use_cases import EnqueueMessageUseCase


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

from flask import (
    Blueprint, Response, request
)

from intergov.monitoring import statsd_timer
from intergov.loggers import logging

from intergov.apis.common.utils import routing


blueprint = Blueprint('message', __name__)
logger = logging.getLogger(__name__)


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

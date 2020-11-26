from flask import (
    Blueprint, Response, request
)

from intergov.apis.common.utils import routing
from intergov.apis.message_rx.conf import Config
from intergov.loggers import logging
from intergov.monitoring import increase_counter
from intergov.monitoring import statsd_timer
from intergov.repos.channel_notifications_inbox import ChannelNotificationRepo
from intergov.use_cases.process_channel_notifications import EnqueueChannelNotificationUseCase
from intergov.use_cases.route_to_channel import get_channel_by_id

blueprint = Blueprint('message', __name__)
logger = logging.getLogger(__name__)


@statsd_timer("api.message_rx.endpoint.channel_message_confirm")
@blueprint.route('/channel-message/<channel_id>', methods=['GET'])
def channel_message_confirm(channel_id):
    """
    Handles subscription verification requests
    https://www.w3.org/TR/websub/#hub-verifies-intent
    hub.mode=subscribe&hub.topic=jurisdiction.AU&
    hub.challenge=e35ad43c-7149-45cb-a8eb-3a5a76a368de&
    hub.lease_seconds=432000
    """
    # TODO: validate topic and mode
    # TODO: validate signature header
    channel = get_channel_by_id(channel_id, Config.ROUTING_TABLE)
    if not channel:
        logger.warning(
            "Trying to confirm subscription for a wrong channel %s (%s)",
            channel_id, Config.ROUTING_TABLE
        )
        return Response("Bad channel_id", status=400)
    increase_counter("message_rx.channel.confirmed")
    return Response(request.args.get('hub.challenge'))


@statsd_timer("api.message_rx.endpoint.channel_message_receive")
@blueprint.route('/channel-message/<channel_id>', methods=['POST'])
@routing.mimetype(['application/json'])
def channel_message_receive(channel_id):
    """
    Handles the pings
    """
    body = request.get_json(silent=True)
    increase_counter("message_rx.message.received")
    repo = ChannelNotificationRepo(
        Config.CHANNEL_NOTIFICATION_REPO_CONF
    )
    use_case = EnqueueChannelNotificationUseCase(channel_notification_repo=repo)
    channel = get_channel_by_id(channel_id, Config.ROUTING_TABLE)
    use_case.execute(channel, body)
    return Response()

from intergov.loggers import logging
from intergov.monitoring import statsd_timer
from intergov.use_cases.common import BaseUseCase

logger = logging.getLogger(__name__)


class RouteToChannelUseCase(BaseUseCase):
    """
    This code makes a routing decision.
    "Which channel should I use to send this message".
    It then pushes the message to that channel.

    As it currently stands,
    the *channel_config* object
    (passed in at construction)
    is a kind of routing table.
    It is an ordered list of channels.
    The router works through the list
    until it finds the first channel
    that does not "screen" the message,
    and uses that channel to deliver the message.

    The channel config is a prototype,
    with hardcoded logic.
    Post POC versions will need a version
    with a configuration system
    that is more friendly to administrators.
    """

    def __init__(self, routing_table):
        self.ROUTING_TABLE = routing_table

    @statsd_timer("usecase.RouteToChannelUseCase.execute")
    def execute(self, message):
        # This is new logic, assuming that channels are dumb.
        # so routing table is a set of scalar values with channel details,
        # and use-case itself does all active (and boring) actions to send message.
        # New logic could be easily converted to the smart channels approach by moving the code.
        super().execute()
        # we return message ID if at least one channel accepted the message and False otherwise
        result = False

        if not self.ROUTING_TABLE:
            logger.warning("Empty routing table provided!")
        for routing_rule in self.ROUTING_TABLE:
            # for all channels we find one which could accept that message
            # based on receiver
            receiver = str(message.receiver)
            if routing_rule["Jurisdiction"] == receiver:
                # this one fits
                channel_instance = routing_rule["ChannelInstance"]
                if channel_instance.screen_message(message):
                    logger.warning(
                        "[%s] Channel %s screens the message",
                        message.sender_ref,
                        routing_rule,
                    )
                    continue
                logger.info(
                    "[%s] Message will be sent to channel %s",
                    message.sender_ref,
                    str(channel_instance),
                )
                channel_result = channel_instance.post_message(message)
                if channel_result:
                    # seems to be a success
                    logger.info(
                        "[%s] Message has been sent to the channel %s with result %s",
                        message.sender_ref,
                        str(channel_instance),
                        channel_result
                    )
                    result = (str(channel_instance), channel_result)
                    break  # don't try to use other channels while at least one succeeded
                else:
                    logger.warning(
                        "[%s] Channel %s didn't accept the message",
                        message.sender_ref,
                        str(channel_instance),
                    )

        return result


def get_channel_by_id(channel_id, routing_table):
    for channel in routing_table:
        if channel['Id'] == channel_id:
            return channel

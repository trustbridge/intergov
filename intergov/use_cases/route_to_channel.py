from intergov.loggers import logging
from intergov.monitoring import statsd_timer

logger = logging.getLogger(__name__)


class RouteToChannelUseCase:
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
        # self.channel_config = channel_config
        # self.channels = []
        # for config in channel_config:
        #     channel = config['type']
        #     self.channels.append(channel(config))

    @statsd_timer("usecase.RouteToChannelUseCase.execute")
    def execute(self, message):
        # This is new logic, assuming that channels are dumb.
        # so routing table is a set of scalar values with channel details,
        # and use-case itself does all active (and boring) actions to send message.
        # New logic could be easily converted to the smart channels approach by moving the code.

        # we return message ID if at least one channel accepted the message and False otherwise
        result = False

        for routing_rule in self.ROUTING_TABLE:
            # for all channels we find one which could accept that message
            # based on receiver
            receiver = str(message.receiver)
            if routing_rule["Jurisdiction"] == receiver:
                # this one fits
                channel_instance = routing_rule["ChannelInstance"]
                if channel_instance.screen_message(message):
                    logger.info(
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

        # Some old logic here
        # for channel in self.channels:
        #     channel_filter = channel.channel_filter
        #     if not channel_filter.screen_message(message):
        #         response = channel.post_message(message)
        #         if isinstance(response, bool):
        #             # such a stupid way to work with things,
        #             # but upper use-case expects that, and some channels return Bool,
        #             # so...
        #             response = (
        #                 '{"status": %s, '
        #                 '"link": "dumbid=http://non-domain.non-tld"}'
        #             ) % 'true' if response else 'false'
        #         return channel.ID, response
        return result

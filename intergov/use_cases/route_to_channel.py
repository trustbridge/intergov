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

    def __init__(self, channel_config):
        self.channels = []
        for config in channel_config:
            channel = config['type']
            self.channels.append(channel(config))

    @statsd_timer("usecase.RouteToChannelUseCase.execute")
    def execute(self, message):
        for channel in self.channels:
            channel_filter = channel.channel_filter
            if not channel_filter.screen_message(message):
                response = channel.post_message(message)
                if isinstance(response, bool):
                    # such a stupid way to work with things,
                    # but upper use-case expects that, and some channels return Bool,
                    # so...
                    response = (
                        '{"status": %s, '
                        '"link": "dumbid=http://non-domain.non-tld"}'
                    ) % 'true' if response else 'false'
                return channel.ID, response

        return False

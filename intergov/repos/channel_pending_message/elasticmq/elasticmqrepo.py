from libtrustbridge.repos.elasticmqrepo import ElasticMQRepo


class ChannelPendingMessageElasticMQRepo(ElasticMQRepo):
    """
    This repo receives pending messages to provide
    them to worker which will poll their status from the
    coresponding channels.
    """

    def _get_queue_name(self):
        return 'channel-pending-messages'

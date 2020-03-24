from intergov.repos.base.elasticmq import elasticmqrepo

"""
This repo receives pending messages to provide
them to worker which will poll their status from the
coresponding channels.
"""


class ChannelPendingMessageElasticMQRepo(elasticmqrepo.ElasticMQRepo):
    def _get_queue_name(self):
        return 'channel-pending-messages'

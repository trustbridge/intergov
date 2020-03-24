from intergov.repos.base.elasticmq import elasticmqrepo

"""
This repo is used to delay message updates
"""


class MessageUpdatesElasticMQRepo(elasticmqrepo.ElasticMQRepo):
    def _get_queue_name(self):
        return 'message-updates'

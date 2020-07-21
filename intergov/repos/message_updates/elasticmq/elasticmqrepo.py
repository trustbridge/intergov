from libtrustbridge.repos.elasticmqrepo import ElasticMQRepo


class MessageUpdatesElasticMQRepo(ElasticMQRepo):
    """
    This repo is used to delay message updates
    """

    def _get_queue_name(self):
        return 'message-updates'

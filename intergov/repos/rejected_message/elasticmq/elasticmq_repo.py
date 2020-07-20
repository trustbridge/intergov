from libtrustbridge.repos.elasticmqrepo import ElasticMQRepo


class RejectedMessagesElasticRepo(ElasticMQRepo):
    def _get_queue_name(self):
        return 'rejected-messages'

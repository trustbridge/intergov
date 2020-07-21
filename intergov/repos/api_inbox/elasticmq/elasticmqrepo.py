from libtrustbridge.repos.elasticmqrepo import ElasticMQRepo


class APIInboxElasticRepo(ElasticMQRepo):
    def _get_queue_name(self):
        return 'api-inbox'

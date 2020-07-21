from libtrustbridge.repos.elasticmqrepo import ElasticMQRepo


class BCInboxRepo(ElasticMQRepo):
    def _get_queue_name(self):
        return 'bc-inbox'

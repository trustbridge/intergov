from intergov.repos.base.elasticmq import elasticmqrepo


class APIInboxElasticRepo(elasticmqrepo.ElasticMQRepo):
    def _get_queue_name(self):
        return 'api-inbox'

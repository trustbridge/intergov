from intergov.repos.base.elasticmq import elasticmqrepo


class BCInboxRepo(elasticmqrepo.ElasticMQRepo):
    def _get_queue_name(self):
        return 'bc-inbox'

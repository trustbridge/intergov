from intergov.repos.base.elasticmq import elasticmqrepo


class RejectedMessagesElasticRepo(elasticmqrepo.ElasticMQRepo):
    def _get_queue_name(self):
        return 'rejected-messages'

from intergov.repos.base.elasticmq import elasticmqrepo


class DeliveryOutboxRepo(elasticmqrepo.ElasticMQRepo):
    def _get_queue_name(self):
        return 'delivery-outbox'

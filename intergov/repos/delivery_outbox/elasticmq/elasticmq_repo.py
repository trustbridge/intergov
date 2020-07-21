from libtrustbridge.repos.elasticmqrepo import ElasticMQRepo


class DeliveryOutboxRepo(ElasticMQRepo):
    def _get_queue_name(self):
        return 'delivery-outbox'

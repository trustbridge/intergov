from libtrustbridge.repos import elasticmqrepo


class NotificationsElasticmqRepo(elasticmqrepo.ElasticMQRepo):
    def _get_queue_name(self):
        return 'notifications'

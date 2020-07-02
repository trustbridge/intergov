from libtrustbridge.repos.elasticmqrepo import ElasticMQRepo


class ChannelNotificationRepo(ElasticMQRepo):
    def _get_queue_name(self):
        return 'channel-notifications-inbox'

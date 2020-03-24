from intergov.repos.base.elasticmq import elasticmqrepo


class ObjectRetrievalRepo(elasticmqrepo.ElasticMQRepo):
    """
    This repo is used to ask Documents Spider to download these objects
    When incoming message is received

    Is populated by message processor (which is universal both for incoming and
    outgoing messages), but only incoming part of it
    """

    def _get_queue_name(self):
        return 'object-retrieval'

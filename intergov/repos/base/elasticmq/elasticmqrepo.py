import json
from intergov.loggers import logging  # NOQA
from intergov.conf import env_bool
import boto3

from intergov.domain.wire_protocols import generic_discrete as message
from intergov.serializers import generic_discrete_message as ser


IGL_ALLOW_UNSAFE_REPO_CLEAR = env_bool('IGL_ALLOW_UNSAFE_REPO_CLEAR', default=False)
IGL_ALLOW_UNSAFE_REPO_IS_EMPTY = env_bool('IGL_ALLOW_UNSAFE_REPO_IS_EMPTY', default=False)


class ElasticMQRepo:

    # This value could be larger for real setups but must be very small
    # for integration tests (otherwise they are unacceptably slow)
    WAIT_FOR_MESSAGE_SECONDS = 5

    def __init__(self, connection_data):
        if connection_data:
            if "elasticmq" in (connection_data.get("host") or ""):
                # smaller for local setups and tests
                self.WAIT_FOR_MESSAGE_SECONDS = 2
            else:
                # bigger for SQS to save requests
                self.WAIT_FOR_MESSAGE_SECONDS = 10
        aws_connection_data = self._aws_connection_data(connection_data)
        connection_data['queue_name'] = connection_data.get('queue_name') or self._get_queue_name()
        if not connection_data['queue_name']:
            raise KeyError('queue_name')
        self.client = boto3.client(
            'sqs',
            **aws_connection_data
        )
        get_url_response = self.client.get_queue_url(
            QueueName=connection_data['queue_name']
        )
        self.queue_url = get_url_response['QueueUrl']

    @staticmethod
    def _aws_connection_data(data):
        use_ssl = data.get('use_ssl', False)
        protocol = 'https' if use_ssl else 'http'
        return {
            'endpoint_url': f"{protocol}://{data['host']}:{data['port']}/",
            'region_name': data['region'],
            'aws_access_key_id': data['access_key'],
            'aws_secret_access_key': data['secret_key'],
            'use_ssl': use_ssl
        }

    def _get_queue_name(self):
        return None  # used purely for tests override this in subclasses for real usage

    def _create_message_object(self, data):
        try:
            return message.Message(
                sender=data["sender"],
                receiver=data["receiver"],
                subject=data["subject"],
                obj=data["obj"],
                predicate=data["predicate"],
                sender_ref=data.get('sender_ref'),
                status=data.get('status')
            )
        except Exception:
            logging.error("Unable to deserealize data %s to Message object", data)
            raise

    def post(self, msg, delay_seconds=0):
        payload = json.dumps(msg, cls=ser.MessageJSONEncoder)
        try:
            self.client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=payload,
                DelaySeconds=delay_seconds)
        except Exception:  # TODO: be specific, what happens when send fails?
            return False
        return True

    def get(self):
        # TODO: consider MaxNumberOfMessages > 1?
        # Warning: always renders a message, so doesn't work with some
        # object containing a message
        response = self.client.receive_message(
            QueueUrl=self.queue_url,
            MessageAttributeNames=['payload'],
            MaxNumberOfMessages=1,
            VisibilityTimeout=30,
            WaitTimeSeconds=self.WAIT_FOR_MESSAGE_SECONDS
        )
        if "Messages" not in response.keys():
            return False
        if len(response["Messages"]) < 1:
            return False

        # we need it just to delete message later
        queue_message_id = response["Messages"][0]["ReceiptHandle"]
        msg = self._create_message_object(
            json.loads(response["Messages"][0]["Body"])
        )
        return (queue_message_id, msg)

    def post_job(self, payload, delay_seconds=0):
        """
        Send arbitrary JSON payload (not a Message object) to a queue
        Usually contains some job to do for some worker
        Also may contain 'message' item with the message, which also will be
        rendered fine and even parsed by a "get_job"
        """
        if not payload:
            raise ValueError('Invalid payload value')
        if not isinstance(delay_seconds, int):
            raise TypeError('Invalid delay_seconds type. Must be int')
        # logging.info("Posting job %s", payload)
        self.client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(payload, cls=ser.MessageJSONEncoder),
            DelaySeconds=delay_seconds
        )
        return True

    def get_job(self):
        # assumes that the queue message is not our Message object
        # but some dict having 'message' item (optionally)
        # used for callbacks, for example
        response = self.client.receive_message(
            QueueUrl=self.queue_url,
            MessageAttributeNames=['payload'],
            MaxNumberOfMessages=1,
            VisibilityTimeout=30,
            WaitTimeSeconds=self.WAIT_FOR_MESSAGE_SECONDS
        )
        if "Messages" not in response.keys():
            return False
        if len(response["Messages"]) < 1:
            return False

        # we need it just to delete message later
        queue_message_id = response["Messages"][0]["ReceiptHandle"]
        payload = json.loads(response["Messages"][0]["Body"])
        # if 'message' in payload:
        #     payload['message'] = self._create_message_object(payload['message'])
        # logging.info("Retrieved job %s", payload)
        return (queue_message_id, payload)

    def delete(self, msg_id):
        try:
            self.response = self.client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=msg_id)
        except Exception:  # TODO be specific
            return False
        return True

    def _unsafe_clear_for_test(self):
        if not IGL_ALLOW_UNSAFE_REPO_CLEAR:
            raise RuntimeError(
                'repo._unsafe_clear_for_test method allowed only when env IGL_ALLOW_UNSAFE_REPO_CLEAR=True'
            )
        self.client.purge_queue(QueueUrl=self.queue_url)

    def _unsafe_is_empty_for_test(self):
        if not IGL_ALLOW_UNSAFE_REPO_IS_EMPTY:
            raise RuntimeError(
                'repo._unsafe_is_empty_for_test method allowed only when env IGL_ALLOW_UNSAFE_REPO_IS_EMPTY=True'
            )
        response = self.client.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=1,
            VisibilityTimeout=0,
            WaitTimeSeconds=self.WAIT_FOR_MESSAGE_SECONDS
        )
        return len(response.get('Messages', [])) == 0

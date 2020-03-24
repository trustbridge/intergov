from io import BytesIO

import boto3
from botocore.client import ClientError

from intergov.conf import env_bool
from intergov.domain.wire_protocols import generic_discrete as message
from intergov.repos.base.minio.minio_objects import Message
from intergov.loggers import logging  # NOQA

logger = logging.getLogger(__name__)

IGL_ALLOW_UNSAFE_REPO_CLEAR = env_bool('IGL_ALLOW_UNSAFE_REPO_CLEAR', default=False)
IGL_ALLOW_UNSAFE_REPO_IS_EMPTY = env_bool('IGL_ALLOW_UNSAFE_REPO_IS_EMPTY', default=False)


def slash_chunk(uri):
    """
    given a URI, returns string like U/R/I
    (with slashes in it).
    This is to prevent a very large number of URIs
    from exhausting the inode pool on some files systems
    when they are saved as files or directory names.
    (because subdirectories could be
    mounted on differnt file systems)
    """
    if len(uri) > 10:
        return '{}/{}'.format(
            uri[:5],
            uri[5:],
        )
    else:
        return uri


class MinioRepo:
    """
    The repo hidding Minio protocol communication inside
    https://docs.min.io/docs/python-client-api-reference.html documentation
    """

    # define it in subclasses, because for most cases it will be the same
    DEFAULT_BUCKET = None

    def __init__(self, connection_data):
        # checking all required props
        connection_data['bucket'] = connection_data.get('bucket') or self.DEFAULT_BUCKET
        if not connection_data['bucket']:
            raise KeyError('bucket')

        aws_connection_data = self._aws_connection_data(connection_data)

        self.client = boto3.client(
            's3',
            **aws_connection_data
        )
        self.bucket = connection_data['bucket']
        self.bucket_name = connection_data['bucket']
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            # The bucket does not exist or you have no access.
            self.client.create_bucket(
                Bucket=self.bucket_name,
                # CreateBucketConfiguration={
                #     'LocationConstraint': connection_data['region']
                # },
            )

    @staticmethod
    def _aws_connection_data(data):
        protocol = 'https' if data['use_ssl'] else 'http'
        return {
            'aws_access_key_id': data['access_key'],
            'aws_secret_access_key': data['secret_key'],
            'endpoint_url': f"{protocol}://{data['host']}:{data['port']}/"
        }

    # seems to be unused
    def _create_message_objects(self, results):  # pragma: no cover
        # TODO: think about moving it somewhere else to mix the
        # business logic with the storage logic less
        return [
            message.Message(
                sender=q.sender,
                receiver=q.receiver,
                subject=q.subject,
                obj=q.obj,
                predicate=q.predicate,
                sender_ref=q.sender_ref)
            for q in results
        ]

    # currently it's a dummy method
    def post_message(self, msg):  # pragma: no cover
        # Warning: seems not to be used anywhere except the tests
        # need to convert from domain message to PG message
        sender = str(msg.sender)
        receiver = str(msg.receiver)
        subject = str(msg.subject)
        obj = str(msg.obj)
        predicate = str(msg.predicate)

        m = Message(
            sender=sender,
            receiver=receiver,
            subject=subject,
            obj=obj,
            predicate=predicate,
            status='pending',
            sender_ref=msg.sender_ref)

        print(m)

        # TODO: figure out the path
        # path = m.path()

        # TODO: ensure the path exists
        # TODO: serialise the message and save it in the path
        # TODO: return some int
        # (is returning an int really a smart API?
        # why not a string)
        # print(self.client.list_buckets())
        return len(self.client.list_buckets())

    def get_object_content(self, path):
        return self.client.get_object(
            Bucket=self.bucket_name,
            Key=path
        )['Body'].read()

    def put_message_related_object(self, sender, sender_ref, rel_path, content_body):
        content_body = content_body.encode("utf-8")
        # this may not be true for the more wide case, but works while senders are countries
        if len(sender) != 2 or sender.upper() != sender:
            raise ValueError('Invalid sender')
        full_path = "{}/{}{}".format(
            sender,
            slash_chunk(sender_ref),
            rel_path
        )
        # logger.info("Saving message, path %s, content_body %s", full_path, content_body)
        # logging.debug("Putting message-related object at %s", full_path)
        return self.client.put_object(
            Bucket=self.bucket_name,
            Key=full_path,
            Body=BytesIO(content_body),
            ContentLength=len(content_body)
        )

    def put_object(self, clean_path=None, chunked_path=None, content_body=None):
        # assert content_body
        if bool(clean_path) == bool(chunked_path):
            raise TypeError('clean_path or chunked_path must be provided')
        content_body = content_body.encode("utf-8")
        # this may not be true for the more wide case, but works while senders are countries
        full_path = chunked_path or slash_chunk(clean_path)
        return self.client.put_object(
            Bucket=self.bucket_name,
            Key=full_path,
            Body=BytesIO(content_body),
            ContentLength=len(content_body)
        )

    # primarily for testing purposes
    # do not use in production code
    def _unsafe_clear_for_test(self):
        if not IGL_ALLOW_UNSAFE_REPO_CLEAR:
            raise RuntimeError(
                'repo._unsafe_clear_for_test method allowed only when env IGL_ALLOW_UNSAFE_REPO_CLEAR=True'
            )
        deleted = 0
        while True:
            response = self.client.list_objects(
                Bucket=self.bucket_name
            )
            for obj in response.get('Contents', []):
                self.client.delete_object(
                    Bucket=self.bucket_name,
                    Key=obj['Key']
                )
                deleted += 1
            if not response['IsTruncated']:
                return deleted

    def _unsafe_is_empty_for_test(self):
        if not IGL_ALLOW_UNSAFE_REPO_IS_EMPTY:
            raise RuntimeError(
                'repo._unsafe_is_empty_for_test method allowed only when env IGL_ALLOW_UNSAFE_REPO_IS_EMPTY=True'
            )
        response = self.client.list_objects(
            Bucket=self.bucket_name
        )
        contents = response.get('Contents', [])
        return len(contents) == 0

    # def put_object_acl(self, path, receiver, content):
    #     # for small objects
    #     # TODO: do we need to really store the whole message twice?
    #     path = slash_chunk(path) + "/" + receiver + ".json"
    #     logging.debug("Putting message ACL for %s at %s", receiver, path)
    #     return self.client.put_object(
    #         bucket_name=self.bucket_name,
    #         object_name=path,
    #         data=BytesIO(content.encode("utf-8")),
    #         length=len(content.encode("utf-8"))
    #     )

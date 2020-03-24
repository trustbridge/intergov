import json
from botocore.client import ClientError
from intergov.domain.wire_protocols import generic_discrete as message
from intergov.repos.base.minio import miniorepo
from intergov.serializers import generic_discrete_message as ser
from intergov.loggers import logging  # NOQA

logger = logging.getLogger(__name__)


class MessageLakeMinioRepo(miniorepo.MinioRepo):

    DEFAULT_BUCKET = 'messagelake'

    def post(self, msg):
        """
        Save message to the lake. Message must have sender and sender_ref fields
        to be searchable. Also the metadata is saved separately.
        """
        assert msg.sender_ref, "sender_ref is required for message to be written"
        content_rendered = json.dumps(msg, cls=ser.MessageJSONEncoder)
        metadata_rendered = json.dumps({
            message.STATUS_KEY: msg.status
        })
        # logging.info(
        #     "Message to be put into the message lake: %s, metadata %s",
        #     content_rendered, metadata_rendered
        # )

        self.put_message_related_object(
            sender=str(msg.sender),
            sender_ref=msg.sender_ref,
            rel_path="/content.json",
            content_body=content_rendered
        )

        self.put_message_related_object(
            sender=str(msg.sender),
            sender_ref=msg.sender_ref,
            rel_path="/metadata.json",
            content_body=metadata_rendered
        )
        return True

    def get(self, sender, sender_ref):
        # try getting /{sender}/{sender_ref}/content.json
        # de-serialise it and return it as native message object
        assert sender and sender_ref
        # logger.info("Retrieving message %s@%s from the message lake", sender, sender_ref)

        content_path = "{}/{}/content.json".format(
            sender,
            miniorepo.slash_chunk(sender_ref)
        )
        metadata_path = "{}/{}/metadata.json".format(
            sender,
            miniorepo.slash_chunk(sender_ref)
        )

        try:
            msg_content = json.loads(
                self.get_object_content(content_path)
            )
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'NoSuchKey':
                logger.error("Retrieve message at %s: no such key", content_path)
                return None
            else:
                raise

        try:
            metadata = json.loads(self.get_object_content(metadata_path))
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'NoSuchKey':
                logger.error("Retrieve message metadata at %s: no such key", metadata_path)
                metadata = None
            else:
                raise

        if metadata:
            for key in [
                message.CHANNEL_ID_KEY,
                message.CHANNEL_TXN_ID_KEY,
                message.STATUS_KEY
            ]:
                # Neketek: I'm not changing approach.
                # What is undefined in metadata will be set to None.
                # But honestly it's cleaner to not include these keys at all.
                # But I'm afraid to break something therefore I leave it as is.
                msg_content[key] = metadata.get(key)

        return message.Message.from_dict(msg_content)

    def update_metadata(self, sender, sender_ref, updates):
        """
        Accepts message details and new metadata fields
        Updates the metadata in the repo
        There is no locking here, so last requester wins due to the storage nature
        """
        metadata_path = "{}/{}/metadata.json".format(
            sender,
            miniorepo.slash_chunk(sender_ref)
        )

        metadata = json.loads(self.get_object_content(metadata_path))
        metadata.update(updates)
        metadata_rendered = json.dumps(metadata)

        return self.put_message_related_object(
            sender=sender,
            sender_ref=sender_ref,
            rel_path="/metadata.json",
            content_body=metadata_rendered
        )

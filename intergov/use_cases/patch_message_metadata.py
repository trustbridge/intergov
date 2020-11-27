from intergov.domain.wire_protocols import generic_discrete as gd
from intergov.loggers import logging  # NOQA
from intergov.monitoring import statsd_timer
from intergov.use_cases.common import BaseUseCase
from intergov.use_cases.common.errors import ConflictError, BadParametersError

logger = logging.getLogger(__name__)


class PatchMessageMetadataUseCase(BaseUseCase):
    """
    Used by the message patch endpoint

    Get the message, update it in the message lake.
    """

    def __init__(self, message_lake_repo, notification_repo):
        self.message_lake = message_lake_repo
        self.notification_repo = notification_repo

    @statsd_timer("usecase.PatchMessageMetadataUseCase.execute")
    def execute(self, reference, payload):
        assert ':' in reference, "sender_ref must be in format AU:XXXX, where AU is a sender"
        super().execute()
        sender, sender_ref = reference.split(':', maxsplit=1)
        # logger.info("Update message %s metadata: %s", reference, payload)
        message = None
        try:
            message = self.message_lake.get(sender, sender_ref)
        except Exception as e:
            if e.__class__.__name__ == 'NoSuchKey':
                message = None
        if not message:
            # Neketek: Here we can throw NotFoundError.
            # But again to not break something which depends on it, I'm leaving it as is.
            logger.error(
                "Tried to retrieve message %s from %s, but no such is found",
                sender_ref, sender,
            )
            return None

        metadata_delta = {}

        new_status = payload.get(gd.STATUS_KEY)
        new_channel_id = payload.get(gd.CHANNEL_ID_KEY)
        new_channel_txn_id = payload.get(gd.CHANNEL_TXN_ID_KEY)

        if new_status and new_status != message.status:
            if message.status in gd.FINAL_STATUSES:
                raise ConflictError(
                    detail=f'Message status is final: {message.status}'
                )
            metadata_delta[gd.STATUS_KEY] = new_status

        if new_channel_id or new_channel_txn_id:
            if new_channel_id and new_channel_txn_id:
                if message.channel_id and message.channel_txn_id:
                    raise ConflictError(f'Message {gd.CHANNEL_ID_KEY} and {gd.CHANNEL_TXN_ID_KEY} already set')
                metadata_delta[gd.CHANNEL_ID_KEY] = new_channel_id
                metadata_delta[gd.CHANNEL_TXN_ID_KEY] = new_channel_txn_id
            else:
                raise BadParametersError(
                    detail=f'Message {gd.CHANNEL_ID_KEY} and {gd.CHANNEL_TXN_ID_KEY} should be only set together.'
                )
        # Neketek: We can raise BadParametersError here but I'll leave it as is
        # because I don't want to break something which depends on it
        if not metadata_delta:
            # return unchanged version of the message
            return message
        # metadata_delta is not empty, perform an update
        self.message_lake.update_metadata(
            sender, sender_ref,
            metadata_delta
        )
        # send status change notification if status updated
        if metadata_delta.get(gd.STATUS_KEY):
            # for customers subscribed on the specific message topics
            # These are light, so containing no useful message information
            # apart of the identifier
            # because subject can contain dots we just remove them
            # (which is fine while subscribers also remove them when subscribing)
            # Also for subject it's logical to subscribe to ".created" instead of ".status"
            # but ".status" also works (if subscribers are aware)
            # self.notification_repo.post_job(
            #     {
            #         gd.SENDER_REF_KEY: str(message.sender_ref),
            #         gd.PREDICATE_KEY: f'message.{str(message.subject).replace(".", "")}.status',
            #         # gd.SUBJECT_KEY: str(message.subject),
            #     }
            # )
            # a normal status change
            self.notification_repo.post_job(
                {
                    gd.PREDICATE_KEY: f'message.{message.sender_ref}.status',
                    gd.SENDER_REF_KEY: f"{message.sender}:{message.sender_ref}"
                    # gd.SUBJECT_KEY: str(message.subject),
                }
            )
        # return updated version of the message
        return self.message_lake.get(sender, sender_ref)

from intergov.monitoring import statsd_timer


class RejectPendingMessageUseCase:
    """
    Gets a single message from rejected message repo
    If rejected message payload is valid - has sender, sender_ref fields
    updates message metadata by changing status to rejected via message lake repo
    update_metadata method

    Fails if:
        1. unable to update message status
        2. rejected message payload is invalid
    """

    def __init__(self, rejected_message_repo, message_lake_repo):
        self.rejected_messages = rejected_message_repo
        self.message_lake = message_lake_repo

    def execute(self):
        update = self.rejected_messages.get()
        if not update:
            return None
        else:
            (upd_id, upd_msg) = update
        return self.process(upd_id, upd_msg)

    @statsd_timer("usecase.RejectPendingMessageUseCase.process")
    def process(self, upd_id, upd_msg):
        delta = {'status': 'rejected'}

        # right now only reason of failure is a critical error
        # NOTE: we need to decide what to do if message not found
        # is it success or critical failure
        try:
            self.message_lake.update_metadata(upd_msg.sender, upd_msg.sender_ref, delta)
        except Exception as e:
            raise Exception(f"Unable to update message status. Reason: {e}") from e

        deleted = self.rejected_messages.delete(upd_id)
        if not deleted:
            return False
        return True

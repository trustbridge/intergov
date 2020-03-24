import time
import requests
from http import HTTPStatus
from intergov.conf import env_queue_config
from intergov.repos.channel_pending_message import ChannelPendingMessageRepo
from intergov.repos.message_updates import MessageUpdatesRepo
from intergov.channels.discrete_generic_memory import DiscreteGenericMemoryhannel
from intergov.domain.wire_protocols import generic_discrete as gd
from intergov.loggers import logging


logger = logging.getLogger('channel_poller_worker')


class ChannelPollerWorker:

    def _prepare_channel_pending_message_repo(self, conf):
        channel_pending_message_repo_conf = env_queue_config('PROC_BCH_CHANNEL_PENDING_MESSAGE')
        if conf:
            channel_pending_message_repo_conf.update(conf)
        self.channel_pending_message_repo = ChannelPendingMessageRepo(channel_pending_message_repo_conf)

    def _prepare_message_updates_repo(self, conf):
        message_updates_repo_conf = env_queue_config('BCH_MESSAGE_UPDATES')
        if conf:
            message_updates_repo_conf.update(conf)
        self.message_updates_repo = MessageUpdatesRepo(message_updates_repo_conf)

    def _poll_message(self, queue_job):
        result = None
        queue_job_id, payload = queue_job
        channel_id = payload['channel_id']
        logger.info(f'Received pending message job for channel:{channel_id}')

        if channel_id == DiscreteGenericMemoryChannel.ID:
            result = self._poll_memory_channel(payload)

        if result:
            logger.info('Job executed successfully. Deleting from queue.')
            return self.channel_pending_message_repo.delete(queue_job_id)
        return False

    def _poll_memory_channel(self, payload):
        resp = requests.get(payload['channel_response']['link'])
        if resp.status_code != HTTPStatus.OK:
            raise RuntimeError("Can't get batch status")
        data = resp.json()
        # getting last data element
        # assuming it's a latest update
        status = data['data'][-1]['status']
        sender_ref = payload['message']['sender_ref']
        sender = payload['message']['sender']
        logger.info(f'Memory channel batch status:{status}')
        if status == 'COMMITTED':
            return self._patch_message_status(sender, sender_ref, 'accepted')
        elif status == 'INVALID':
            return self._patch_message_status(sender, sender_ref, 'rejected')
        else:
            return False

    def _patch_message_status(self, sender, sender_ref, status):
        job = {
            'message': {
                gd.SENDER_KEY: sender,
                gd.SENDER_REF_KEY: sender_ref
            },
            'patch': {
                gd.STATUS_KEY: status
            }
        }
        logger.info(f'Sending job to channel message updater:{job}')
        return self.message_updates_repo.post_job(job, delay_seconds=10)

    def __init__(
        self,
        channel_pending_message_repo_conf=None,
        message_updates_repo_conf=None
    ):
        self._prepare_channel_pending_message_repo(channel_pending_message_repo_conf)
        self._prepare_message_updates_repo(message_updates_repo_conf)

    def __iter__(self):
        logger.info('Starting channel poller worker')
        return self

    def __next__(self):
        try:
            queue_job = self.channel_pending_message_repo.get_job()
            if not queue_job:
                return None
            return self._poll_message(queue_job)
        except Exception as e:  # pragma: no cover
            logger.exception(e)
        return None


if __name__ == '__main__':  # pragma: no cover
    for result in ChannelPollerWorker():
        if result is None:
            time.sleep(1)

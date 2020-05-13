import time
import requests
from http import HTTPStatus
from intergov.conf import env_queue_config
from intergov.repos.message_updates import MessageUpdatesRepo
from intergov.domain.wire_protocols import generic_discrete as gd
from intergov.loggers import logging
from intergov.processors.common.env import (
    MESSAGE_PATCH_API_ENDPOINT
)

logger = logging.getLogger('channel_message_updater')


class MessageUpdater(object):
    """
    Iterate over message update jobs:

    * get a job from the queue
    * after some job validation, update the message using the API
    * if sucessful, delete the job from the queue
    * if unsucessful, increment retry counter and reschedule attempt
    """
    # TODO: FIXME: push business logic into a testable use_case object
    # maybe also put the "update job" into a request model
    # TODO: tar-pit algorithm on retrys?
    # (prevent thundering herd after outage)
    def _prepare_message_updates_repo(self, conf):
        message_updates_repo_conf = env_queue_config('BCH_MESSAGE_UPDATES')
        if conf:
            message_updates_repo_conf.update(conf)
        self.message_updates_repo = MessageUpdatesRepo(message_updates_repo_conf)

    def _patch_message(self, job):
        msg = job['message']
        patch = job['patch']
        retry = job.get('retry', 0)
        retry_max = job.get('retry_max', 2)
        sender = msg[gd.SENDER_KEY]
        sender_ref = msg[gd.SENDER_REF_KEY]
        logger.info(
            'Patching message[sender:%s, sender_ref:%s, patch:%s]',
            sender,
            sender_ref,
            patch
        )
        resp = requests.patch(
            MESSAGE_PATCH_API_ENDPOINT.format(
                sender=sender,
                sender_ref=sender_ref
            ),
            json=patch
        )
        if resp.status_code == HTTPStatus.NOT_FOUND:
            if retry + 1 > retry_max:
                # this should probably be at least WARN level
                logger.warning('[%s] Message not found. Max retries reached.', sender_ref)
                return True
            logger.warning('[%s] Message not found. Schedule retry', sender_ref)
            job['retry'] = retry + 1
            self.message_updates_repo.post_job(job, delay_seconds=30)
            return True
        if resp.status_code == HTTPStatus.CONFLICT:
            logger.warning('[%s] Patch causing conflict with the current message state.', sender_ref)
            return True
        if resp.status_code != HTTPStatus.OK:
            retry_number = retry + 1
            logger.error(
                "[%s] Can't patch the message: %s; sheduling retry %s of %s",
                sender_ref, resp.text, retry_number, retry_max,
            )
            job['retry'] = retry_number
            self.message_updates_repo.post_job(job, delay_seconds=30)
            return True
        logger.info('[%s] Message patched successfully.', sender_ref)
        return True

    def __init__(
        self,
        message_updates_repo_conf=None
    ):
        self._prepare_message_updates_repo(message_updates_repo_conf)

    def __iter__(self):
        logger.info('Starting channel message updater')
        return self

    def __next__(self):
        try:
            result = self.message_updates_repo.get_job()
            if not result:
                return None
            job_queue_id, job_payload = result
            if self._patch_message(job_payload):
                logger.info('Deleting the job.')
                return self.message_updates_repo.delete(job_queue_id)
        except Exception as e:
            logger.exception(e)
            return None


if __name__ == '__main__':
    for result in MessageUpdater():
        if result is None:
            time.sleep(1)

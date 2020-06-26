import time
import requests
from http import HTTPStatus
from intergov.apis.common.interapi_auth import AuthMixin
from intergov.conf import env_queue_config
from intergov.domain.wire_protocols import generic_discrete as gd
from intergov.repos.message_updates import MessageUpdatesRepo
from intergov.loggers import logging
from intergov.processors.common.env import (
    MESSAGE_PATCH_API_ENDPOINT,
    MESSAGE_PATCH_API_ENDPOINT_AUTH,
)
from intergov.processors.common.utils import get_message_patch_api_endpoint_auth_params

logger = logging.getLogger('message_updater')


class MessageUpdater(AuthMixin, object):
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

    def _get_headers_for_message_api(self):
        result = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if MESSAGE_PATCH_API_ENDPOINT_AUTH == "none":
            auth_parameters = None
        elif MESSAGE_PATCH_API_ENDPOINT_AUTH == "Cognito/JWT":
            auth_parameters = get_message_patch_api_endpoint_auth_params()
        else:
            raise Exception(f"Unsupported endpoint auth {MESSAGE_PATCH_API_ENDPOINT_AUTH}")
        result.update(self._get_auth_headers(
            auth_method=MESSAGE_PATCH_API_ENDPOINT_AUTH,
            # auth well known urls and other configuration
            auth_parameters=auth_parameters
        ))
        return result

    def _patch_message(self, job):
        msg = job['message']
        patch_payload = job['patch']
        retry = job.get('retry', 0)
        retry_max = job.get('retry_max', 5)
        sender = msg[gd.SENDER_KEY]
        sender_ref = msg[gd.SENDER_REF_KEY]
        logger.info(
            'Patching message[sender:%s, sender_ref:%s, patch:%s]',
            sender,
            sender_ref,
            patch_payload
        )
        resp = requests.patch(
            MESSAGE_PATCH_API_ENDPOINT.format(
                sender=sender,
                sender_ref=sender_ref
            ),
            json=patch_payload,
            headers=self._get_headers_for_message_api(),
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
            if retry_number <= retry_max:
                logger.error(
                    "[%s] Can't patch the message: %s; sheduling retry %s of %s",
                    sender_ref, resp.text, retry_number, retry_max,
                )
                job['retry'] = retry_number
                self.message_updates_repo.post_job(job, delay_seconds=30)
                return True
            else:
                logger.error(
                    "[%s] Can't patch the message: %s; dropping - max retries reached",
                    sender_ref, resp.text
                )
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

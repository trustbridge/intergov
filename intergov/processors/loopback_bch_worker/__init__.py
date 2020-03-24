"""
Quite dumb blockchain worker.
It doesn't call any use-cases because of its nature, used only for the local
demo and development purposes.

Gets pending messages from the ApiOutboxRepo
Marks them as 'sending' in the local postgres storage
(real blockchain work goes here)
Changes their status in the message_rx_api to "accepted"
Marks them as 'accepted' in the local postgres storage

Real worker would call real blockchain procedures instead.
"""
import random
import time

import requests

from intergov.conf import env, env_queue_config, env_postgres_config
from intergov.repos.api_outbox import ApiOutboxRepo
from intergov.repos.rejected_message import RejectedMessagesRepo
from intergov.loggers import logging

logger = logging.getLogger('loopback_bch_worker')


class LoopbackBlockchainWorker(object):

    REJECT_EACH = int(env(
        'IGL_PROC_LOOPBACK_BCH_WORKER_REJECT_EACH',
        default=0
    ))

    MESSAGE_PATCH_API_ENDPOINT = env(
        'IGL_PROC_BCH_MESSAGE_API_ENDPOINT',
        default='http://message_api:5101/message/{sender}:{sender_ref}'
    )

    MESSAGE_RX_API_ENDPOINT = env(
        'IGL_PROC_BCH_MESSAGE_RX_API_URL',
        default='http://message_rx_api:5100/messages'
    )

    # default for all instances
    rejected_each_counter = 0

    def __init__(self,  blockchain_outbox_repo_conf=None, rejected_messages_repo_conf=None):
        self._prepare_blockchain_repo(blockchain_outbox_repo_conf)
        self._prepare_rejected_messages_repo(rejected_messages_repo_conf)

    def _prepare_blockchain_repo(self, config=None):
        blockchain_outbox_repo_conf = env_postgres_config('PROC_BCH_OUTBOX_REPO')
        if config:
            blockchain_outbox_repo_conf.update(config)
        self.blockchain_outbox_repo = ApiOutboxRepo(blockchain_outbox_repo_conf)

    def _prepare_rejected_messages_repo(self, config=None):
        rejected_messages_repo_conf = env_queue_config('PROC_REJECTED_MESSAGES_REPO')
        if config:
            rejected_messages_repo_conf.update(config)
        self.rejected_messages_repo = RejectedMessagesRepo(rejected_messages_repo_conf)

    def __iter__(self):
        logger.info("Starting the loopback blockchain worker")
        return self

    def __next__(self):
        try:
            result = self._process_next_message()
        except Exception as e:
            logger.exception(e)
            result = None
        return result

    def _create_message_payload(self, msg):
        return {
            'sender': msg.sender,
            'receiver': msg.receiver,
            'subject': msg.subject,
            'obj': msg.obj,
            'sender_ref': msg.sender_ref,
            'predicate': msg.predicate,
        }

    def _patch_message_status(self, msg, status):
        url = self.MESSAGE_PATCH_API_ENDPOINT.format(
            sender=msg.sender,
            sender_ref=msg.sender_ref
        )
        logger.info("Patching message status to %s by url %s", status, url)
        resp = requests.patch(
            url,
            json={
                'status': status
            }
        )
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                "Unable to patch message status, resp code {} body {}".format(
                    resp.status_code, resp.content
                )
            )

    def _post_message_rx(self, payload):
        resp = requests.post(
            self.MESSAGE_RX_API_ENDPOINT,
            json=payload
        )
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                "Unable to post message, code {}, resp {}".format(
                    resp.status_code, resp.content
                )
            )
        return resp

    def _process_next_message(self):
        msg = self.blockchain_outbox_repo.get_next_pending_message()
        if msg is None:
            return None
        # ensure message got to the repo as expected, won't be a problem for prod
        # (remove it there)
        # time.sleep(3)
        logger.info("[Loopback] Processing message %s (%s) to the blockchain", msg, msg.id)
        # dummy reject controllable from env variable "IGL_PROC_LOOPBACK_BCH_WORKER_REJECT_EACH"
        if self.REJECT_EACH > 0:
            self.rejected_each_counter += 1
            if self.rejected_each_counter == self.REJECT_EACH:
                logger.info(
                    "Rejecting the message (because we reject one of %s, and this is %s)",
                    self.REJECT_EACH,
                    self.rejected_each_counter
                )
                self.rejected_each_counter = 0
                self.blockchain_outbox_repo.patch(msg.id, {'status': 'rejected'})
                self.rejected_messages_repo.post(msg)
                return True

        self.blockchain_outbox_repo.patch(msg.id, {'status': 'sending'})
        # time.sleep(1)  # for the realistic debug

        # please note that logically we don't forward message
        # but send a message about the message which is equal to the message
        # so we don't re-send the same object,
        # but we send another object which (wow!) has all fields the same
        # but it's not the same, because we logically got it from the
        # blockchain, where it was encrypted/compressed and abused by other methos
        message_to_be_sent = self._create_message_payload(msg)
        # it's a silly situation when importer app in the same intergov setup
        # gets both messages, but in the real situation remote importer_app
        # will get only the blockchain one.

        logger.info("message_to_be_sent %s", message_to_be_sent)
        # we behave like this message has been received from the remote party
        self._post_message_rx(message_to_be_sent)
        self.blockchain_outbox_repo.patch(msg.id, {'status': 'accepted'})
        # now we update the original message status
        self._patch_message_status(msg, 'accepted')

        logger.info(
            "[Loopback] The message has been sent to blockchain and "
            "immediately retrieved from it as a received"
        )
        return True


if __name__ == '__main__':   # pragma: no cover
    for result in LoopbackBlockchainWorker():
        if result is None:
            time.sleep(random.randint(1, 5) / 3.0)

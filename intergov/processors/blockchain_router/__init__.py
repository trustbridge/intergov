"""
Gets pending messages from the ApiOutboxRepo
Marks them as 'sending' in the local postgres storage
(real blockchain work goes here)
Changes their status in the message_rx_api to "accepted"
Marks them as 'accepted' in the local postgres storage

"""
import copy
import json
import random
import time

from intergov.conf import env, env_postgres_config, env_queue_config
from intergov.repos.api_outbox import ApiOutboxRepo
from intergov.repos.channel_pending_message import ChannelPendingMessageRepo
from intergov.repos.message_updates import MessageUpdatesRepo
from intergov.loggers import logging
from intergov.domain.wire_protocols import generic_discrete as gd
from intergov.use_cases.route_to_channel import RouteToChannelUseCase
from intergov.channels.discrete_generic_memory import DiscreteGenericMemoryChannel

logger = logging.getLogger('multichannel_bch_worker')

# this is a kludge
# we need some kind of configured registry
DEFAULT_CONFIG = [
    {
        'id': 'DiscreteGenericMemoryChannel',
        'type': DiscreteGenericMemoryChannel,
    }
]


class MultiChannelBlockchainWorker(object):
    """
    Iterate over the RouteToChannelUseCase.
    """
    def _prepare_config(self, config):
        if config:
            self.config = config
        else:
            self.config = copy.deepcopy(DEFAULT_CONFIG)

    def _prepare_blockchain_outbox_repo(self, conf):
        blockchain_outbox_repo_conf = env_postgres_config('PROC_BCH_OUTBOX')
        if conf:
            blockchain_outbox_repo_conf.update(conf)
        self.blockchain_outbox_repo = ApiOutboxRepo(blockchain_outbox_repo_conf)

    def _prepare_message_updates_repo(self, conf):
        message_updates_repo_conf = env_queue_config('BCH_MESSAGE_UPDATES')
        if conf:
            message_updates_repo_conf.update(conf)
        self.message_updates_repo = MessageUpdatesRepo(message_updates_repo_conf)

    def _prepare_channel_pending_message_repo(self, conf):
        channel_pending_message_repo_conf = env_queue_config('PROC_BCH_CHANNEL_PENDING_MESSAGE')
        if conf:
            channel_pending_message_repo_conf.update(conf)
        self.channel_pending_message_repo = ChannelPendingMessageRepo(channel_pending_message_repo_conf)

    def _prepare_use_cases(self):
        self.uc = RouteToChannelUseCase(self.config)

    def _message_to_dict(self, msg):
        return {
            gd.SENDER_KEY: msg.sender,
            gd.RECEIVER_KEY: msg.receiver,
            gd.SUBJECT_KEY: msg.subject,
            gd.OBJ_KEY: msg.obj,
            gd.PREDICATE_KEY: msg.predicate,
            gd.SENDER_REF_KEY: msg.sender_ref
        }

    def _push_message_to_channel_pending_message_repo(self, channel_id, channel_response, msg):
        if channel_id == DiscreteGenericMemoryChannel.ID:
            return self.channel_pending_message_repo.post_job(
                {
                    'channel_id': channel_id,
                    'channel_response': json.loads(channel_response),
                    'message': self._message_to_dict(msg)
                }
            )
        return False

    def _push_message_to_channel_message_updater(self, channel_id, channel_response, msg):
        if channel_id == DiscreteGenericMemoryChannel.ID:
            channel_response = json.loads(channel_response)
            channel_txn_id = channel_response['link'].split('=')[1]
        else:
            return False
        return self.message_updates_repo.post_job(
            {
                'message': self._message_to_dict(msg),
                'patch': {
                    gd.CHANNEL_ID_KEY: channel_id,
                    gd.CHANNEL_TXN_ID_KEY: channel_txn_id
                }
            },
            delay_seconds=10
        )

    def __init__(
        self,
        blockchain_outbox_repo_conf=None,
        channel_pending_message_repo_conf=None,
        message_updates_repo_conf=None,
        config=None
    ):
        self._prepare_config(config)
        self._prepare_blockchain_outbox_repo(blockchain_outbox_repo_conf)
        self._prepare_channel_pending_message_repo(channel_pending_message_repo_conf)
        self._prepare_message_updates_repo(message_updates_repo_conf)
        self._prepare_use_cases()

    def __iter__(self):
        logger.info("Starting the multichannel blockchain worker")
        return self

    def __next__(self):
        try:

            msg = self.blockchain_outbox_repo.get_next_pending_message()
            if not msg:
                return None
            logger.info("Processing message %s (%s)", msg, msg.id)
            self.blockchain_outbox_repo.patch(msg.id, {'status': 'sending'})

            # If not result message wasn't posted to channel
            # it looks like ok situation from the use case point of view
            # therefore we just silently return None
            # BUT we probably want to change status of the message in
            # blockchain_outbox_repo

            try:
                result = self.uc.execute(msg)
            except Exception:
                time.sleep(random.randint(1, 6))
                raise
            if not result:
                return None
            channel_id, channel_response = result
            logger.info(f'Channel[{channel_id}]: {channel_response}')

            self._push_message_to_channel_pending_message_repo(channel_id, channel_response, msg)
            self._push_message_to_channel_message_updater(channel_id, channel_response, msg)

            if self.blockchain_outbox_repo.patch(msg.id, {'status': 'accepted'}):
                logger.info("The message has been sent to channel")
            else:
                logger.info("The message has been sent but failed to update msg in outbox")
                return False

        except Exception as e:
            logger.exception(e)
            return None
        return True


if __name__ == '__main__':  # pragma: no cover
    # To start it manually, from the base dir:
    # export IGL_PROC_BCH_OUTBOX_REPO_HOST=127.0.0.1
    # export IGL_PROC_BCH_OUTBOX_REPO_USER=postgres
    # export IGL_PROC_BCH_OUTBOX_REPO_DBNAME=api_outbox
    # export IGL_PROC_BCH_MESSAGE_RX_API_URL="http://localhost:5100/messages"
    # PYTHONPATH="`pwd`" python intergov/processors/loopback_bch_worker/__init__.py
    for result in MultiChannelBlockchainWorker():
        if result is None:
            time.sleep(1)

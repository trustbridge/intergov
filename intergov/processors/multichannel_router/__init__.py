"""
* Get pending messages from the ApiOutboxRepo
* Mark them as 'sending' in the local storage
* Pick a channel
* Send them to the channel
* Change their status in the message_rx_api to "accepted" (?)
* Marks them as 'accepted' in the local storage

local storage - postgres for example (and for the demo)
"""
import random
import time

from intergov.conf import env_postgres_config, env
from intergov.channels.http_api_channel import HttpApiChannel
from intergov.repos.api_outbox import ApiOutboxRepo
from intergov.repos.api_outbox.postgres_objects import Message as PostgresMessageRepr
from intergov.loggers import logging
from intergov.domain.wire_protocols import generic_discrete as gd
from intergov.use_cases.route_to_channel import RouteToChannelUseCase

logger = logging.getLogger('multichannel_router')

# Commented out because we decided not to use memory channel for some time
# # this is a kludge
# # we need some kind of configured registry
# DEFAULT_CONFIG = [
#     {
#         'id': 'DiscreteGenericMemoryChannel',
#         'type': DiscreteGenericMemoryChannel,
#     }
# ]


class MultichannelWorker(object):
    """
    Iterate over the RouteToChannelUseCase.
    """

    ROUTING_TABLE = [
        {
            "Name": "shared db channel to Australia",  # any text
            # these 2 are for routing the messages
            "Jurisdiction": "AU",  # please add more countries if you need to
            "Predicate": "UN.CEFACT.",  # quite wide
            # everything after this ponit is channel-specific configuration
            "ChannelUrl": env(
                "IGL_MCHR_SHARED_CHANNEL_URL",
                default="https://sharedchannel.services.devnet.trustbridge.io/"
            ),
            "ChannelAuth": "Cognito/JWT",  # a simplifed approach
        },
        {
            "Name": "shared db channel to Singapore",
            "Jurisdiction": "SG",
            "Predicate": "UN.CEFACT.",
            "ChannelUrl": env(
                "IGL_MCHR_SHARED_CHANNEL_URL",
                default="https://sharedchannel.services.devnet.trustbridge.io/"
            ),
            "ChannelAuth": "Cognito/JWT",
        },
        {
            "Name": "dumb SG channel",
            "Jurisdiction": "FR",
            "Predicate": "UN.CEFACT.",
            "ChannelUrl": env(
                "IGL_MCHR_SHARED_CHANNEL_URL",
                default="http://httpbin.org/"
            ),
            "ChannelAuth": "None",
        },
    ]

    # def _prepare_config(self, config):
    #     if config:
    #         self.config = config
    #     else:
    #         self.config = copy.deepcopy(DEFAULT_CONFIG)

    def _prepare_outbox_repo(self, conf):
        outbox_repo_conf = env_postgres_config('PROC_BCH_OUTBOX')
        if conf:
            outbox_repo_conf.update(conf)
        self.outbox_repo = ApiOutboxRepo(outbox_repo_conf)

    # def _prepare_message_updates_repo(self, conf):
    #     message_updates_repo_conf = env_queue_config('BCH_MESSAGE_UPDATES')
    #     if conf:
    #         message_updates_repo_conf.update(conf)
    #     self.message_updates_repo = MessageUpdatesRepo(message_updates_repo_conf)

    # def _prepare_channel_pending_message_repo(self, conf):
    #     channel_pending_message_repo_conf = env_queue_config('PROC_BCH_CHANNEL_PENDING_MESSAGE')
    #     if conf:
    #         channel_pending_message_repo_conf.update(conf)
    #     self.channel_pending_message_repo = ChannelPendingMessageRepo(channel_pending_message_repo_conf)

    def _prepare_use_cases(self):
        self.uc = RouteToChannelUseCase(self.ROUTING_TABLE)

    def _prepare_channels(self):
        """
        For each channel in the use-case we create channel object
        and put it into the route table; so underlying use-cases
        don't think about it at all and just use the object.
        """
        for routing_rule in self.ROUTING_TABLE:
            routing_rule["ChannelInstance"] = HttpApiChannel(routing_rule.copy())
        return

    def _message_to_dict(self, msg):
        return {
            gd.SENDER_KEY: msg.sender,
            gd.RECEIVER_KEY: msg.receiver,
            gd.SUBJECT_KEY: msg.subject,
            gd.OBJ_KEY: msg.obj,
            gd.PREDICATE_KEY: msg.predicate,
            gd.SENDER_REF_KEY: msg.sender_ref
        }

    # def _push_message_to_channel_pending_message_repo(self, channel_id, channel_response, msg):
    #     if channel_id == DiscreteGenericMemoryChannel.ID:
    #         return self.channel_pending_message_repo.post_job(
    #             {
    #                 'channel_id': channel_id,
    #                 'channel_response': json.loads(channel_response),
    #                 'message': self._message_to_dict(msg)
    #             }
    #         )
    #     return False

    # def _push_message_to_channel_message_updater(self, channel_id, channel_response, msg):
    #     if channel_id == DiscreteGenericMemoryChannel.ID:
    #         channel_response = json.loads(channel_response)
    #         channel_txn_id = channel_response['link'].split('=')[1]
    #     else:
    #         return False
    #     return self.message_updates_repo.post_job(
    #         {
    #             'message': self._message_to_dict(msg),
    #             'patch': {
    #                 gd.CHANNEL_ID_KEY: channel_id,
    #                 gd.CHANNEL_TXN_ID_KEY: channel_txn_id
    #             }
    #         },
    #         delay_seconds=10
    #     )

    def __init__(
        self,
        outbox_repo_conf=None,
        channel_pending_message_repo_conf=None,
        message_updates_repo_conf=None,
        config=None
    ):
        # self._prepare_config(config)
        self._prepare_outbox_repo(outbox_repo_conf)
        # self._prepare_channel_pending_message_repo(channel_pending_message_repo_conf)
        # self._prepare_message_updates_repo(message_updates_repo_conf)
        self._prepare_use_cases()
        self._prepare_channels()

    def __iter__(self):
        logger.info(
            "Starting the multichannel worker with channels %s",
            [ch["Name"] for ch in self.ROUTING_TABLE]
        )
        return self

    def __next__(self):
        try:
            pg_msg = self.outbox_repo.get_next_pending_message()
            if not pg_msg:
                return None
            logger.info("Processing message %s (%s)", pg_msg, pg_msg.id)
            self.outbox_repo.patch(pg_msg.id, {'status': 'sending'})

            # If not result message wasn't posted to channel
            # it looks like ok situation from the use case point of view
            # therefore we just silently return None
            # BUT we probably want to change status of the message in
            # outbox_repo

            # first we convert message from the
            # intergov.repos.api_outbox.postgres_objects.Message
            # to
            # intergov.domain.wire_protocolsgeneric_discrete.Message
            # (actual while we use postgres as a storage for outbox repo)
            assert isinstance(pg_msg, PostgresMessageRepr)
            gd_msg = gd.Message.from_dict(
                pg_msg.to_dict()
            )

            try:
                result = self.uc.execute(gd_msg)
            except Exception as e:
                # sleep some seconds after fails
                logger.info(
                    "[%s] Rejecting due to use-case exception %s",
                    gd_msg.sender_ref,
                    str(e)
                )
                self.outbox_repo.patch(pg_msg.id, {'status': 'rejected'})
                for i in range(random.randint(30, 100)):
                    time.sleep(0.1)
                return False

            if result:
                # message has been sent somewhere
                logger.info("[%s] The message has been sent to channel", gd_msg.sender_ref)
                if not self.outbox_repo.patch(pg_msg.id, {'status': 'accepted'}):
                    logger.warning("[%s] Failed to update msg in outbox", gd_msg.sender_ref)
                    result = False
                else:
                    result = True
            else:
                # no channel accepted the message or there was other error
                logger.info("[%s] Message has NOT been sent", gd_msg.sender_ref)
                self.outbox_repo.patch(pg_msg.id, {'status': 'rejected'})
                result = False

            logger.warning(
                "[%s] Although we have updated status of the message  - "
                "nobody knows about that (need to send that WebSub event)",
                gd_msg.sender_ref
            )
            # TODO: now we send event about message {gd_msg.sender_ref}
            # (light), so any interested party can re-retrieve it and do something
            # first use case: chambers app sent the message gets that update and
            # understands that status has changed from "pending" tp "sent/rejected"
            return result

        except Exception as e:
            logger.exception(e)
            return None
        return True


if __name__ == '__main__':  # pragma: no cover
    for result in MultichannelWorker():
        if result is None:
            for i in range(10):
                time.sleep(0.1)

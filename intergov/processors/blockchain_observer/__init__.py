import time
import hashlib
import uuid
import zmq
import datetime
import requests
from http import HTTPStatus

from events_pb2 import EventSubscription, EventFilter, EventList
from client_event_pb2 import ClientEventsSubscribeRequest, ClientEventsSubscribeResponse
from network_pb2 import PingRequest
from validator_pb2 import Message
import transaction_receipt_pb2


from intergov.domain.wire_protocols import generic_discrete as gd
from intergov.conf import env
from intergov.loggers import logging
from intergov.processors.common.env import (
    MESSAGE_RX_API_URL,
)

logger = logging.getLogger('bch_observer')

DEFAULT_IGL_COUNTRY = 'AU'
IGL_COUNTRY = env('IGL_COUNTRY', default=None)
if IGL_COUNTRY is None:
    logger.warning(f'IGL_COUNTRY is undefined using {DEFAULT_IGL_COUNTRY}')
    IGL_COUNTRY = DEFAULT_IGL_COUNTRY


CONNECT_FQDN = env(
    'CONNECT_FQDN',
    default="memory-validator-default"
)


# TODO: this is the creation of the subscription request, we probably want to create
# a list of subscriptions based on some configuration (per channel). things that vary
# would be the event_type and the match string (the match string is transaction processor specific)

TP_NAMESPACE = hashlib.sha512('generic-discrete-message'.encode("utf-8")).hexdigest()[0:6]
SUBSCRIPTION = EventSubscription(
    event_type="memory/state-delta",
    filters=[
        EventFilter(
            key="address",
            match_string="%s.*" % TP_NAMESPACE,
            filter_type=EventFilter.REGEX_ANY
        )
    ]
)
SUBSCRIPTION_REQUEST = ClientEventsSubscribeRequest(subscriptions=[SUBSCRIPTION]).SerializeToString()
SUBSCRIPTION_RESPONSE_TIMEOUT = 60

# ping each 60 seconds of idle
IDLE_PING_INTERVAL = 60
PING_TIMEOUT = 60


class BlockchainObserverWorker(object):

    def _create_socket(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)

    def _connect_socket(self):
        self.url = f"tcp://{CONNECT_FQDN}:4004"
        self.socket.connect(self.url)
        logger.info(f'Connecting to {self.url}')

    def _parse_message(self, data):
        msg = Message()
        msg.ParseFromString(data)
        return msg

    def _receive_message(self, **kwargs):
        data = self.socket.recv_multipart(**kwargs)[-1]
        self._update_message_received_time()
        return self._parse_message(data)

    def _check_subscription_response(self, msg):
        if msg.message_type != Message.MessageType.CLIENT_EVENTS_SUBSCRIBE_RESPONSE:
            logger.error(msg)
            raise RuntimeError('Message.message_type is invalid. Excpected CLIENT_EVENTS_SUBSCRIBE_RESPONSE')
        subscription_response = ClientEventsSubscribeResponse()
        subscription_response.ParseFromString(msg.content)
        if subscription_response.status != ClientEventsSubscribeResponse.Status.OK:
            logger.error(msg)
            raise RuntimeError('ClientEventsSubscribeResponse.status is not OK')
        logger.info("Subscription response received. Successfully subscribed to events.")

    def _get_client_events_from_msg(self, msg):
        if msg.message_type != Message.MessageType.CLIENT_EVENTS:
            raise ValueError('Invalid message type')
        events = EventList()
        events.ParseFromString(msg.content)
        return events

    # will be set after subscription response received
    def _update_message_received_time(self):
        self._message_received_time = datetime.datetime.utcnow()

    def _should_ping(self):
        message_received_seconds_ago = (datetime.datetime.utcnow() - self._message_received_time).seconds
        return message_received_seconds_ago >= IDLE_PING_INTERVAL

    def _ping(self):
        msg = Message(
            message_type=Message.MessageType.PING_REQUEST,
            content=PingRequest().SerializeToString()
        ).SerializeToString()
        logger.info("Pinging socket...")
        self.socket.send_multipart([msg])
        for i in range(PING_TIMEOUT):
            time.sleep(1)
            try:
                msg = self._receive_message(flags=zmq.NOBLOCK)
                logger.info('Ping response received. Continuing regular workflow.')
            except zmq.Again:
                pass
        else:
            raise RuntimeError("Ping timeout. Probably connection is lost.")

    def _subscribe_to_events(self):
        msg = Message(
            correlation_id=str(uuid.uuid4()),
            message_type=Message.MessageType.CLIENT_EVENTS_SUBSCRIBE_REQUEST,
            content=SUBSCRIPTION_REQUEST
        ).SerializeToString()

        logger.info("Sending subscription request...")
        self.socket.send_multipart([msg])
        logger.info("Subscription request sent. Waiting for response...")
        for i in range(SUBSCRIPTION_RESPONSE_TIMEOUT):
            time.sleep(1)
            try:
                msg = self._receive_message(flags=zmq.NOBLOCK)
                self._check_subscription_response(msg)
                return
            except zmq.Again:
                pass
        else:
            raise RuntimeError("Unable to receive subscription response. Time Out.")

    def _generate_message_dict_from_state_change(self, state_change):
        values = state_change.value.decode().split(",")
        sender_ref, subject, obj, predicate, sender, receiver = values
        message_dict = {
            gd.SENDER_KEY: sender,
            gd.RECEIVER_KEY: receiver,
            gd.PREDICATE_KEY: predicate,
            gd.OBJ_KEY: obj,
            gd.SUBJECT_KEY: subject,
            gd.SENDER_REF_KEY: sender_ref
        }
        return message_dict

    def _post_message_to_message_rx(self, payload):
        logger.info(f'Posting message to message_rx_api:{payload}')
        resp = requests.post(
            '%s/messages' % MESSAGE_RX_API_URL,
            json=payload
        )
        if resp.status_code != HTTPStatus.CREATED:
            raise RuntimeError(
                "Unable to post message, resp code {} body {}".format(
                    resp.status_code, resp.content
                )
            )
        logger.info('Message posted successfully')

    def __init__(self):
        self._create_socket()
        self._connect_socket()
        self._subscribe_to_events()

    def __iter__(self):
        logger.info('Listening for events')
        return self

    def __next__(self):
        try:
            # uncomment this to get regular pings of the hub
            # when no events received for IDLE_PING_INTERVAL
            # currently validator has no handler for this message type
            # but should
            # if self._should_ping():
            #     msg = self._ping()
            # else:
            msg = self._receive_message(flags=zmq.NOBLOCK)
            # logger.info(f"Received message => \n{msg}")
            events_list = self._get_client_events_from_msg(msg)
        except (zmq.Again, ValueError):
            return None
        for event in events_list.events:
            state_change_list = transaction_receipt_pb2.StateChangeList()
            state_change_list.ParseFromString(event.data)
            for state_change in state_change_list.state_changes:
                try:
                    message_dict = self._generate_message_dict_from_state_change(state_change)
                    sender = message_dict['sender']
                    if sender != IGL_COUNTRY:
                        self._post_message_to_message_rx(message_dict)

                except (RuntimeError, ValueError) as e:
                    logger.exception(e)
                    return None
        return True


for result in BlockchainObserverWorker():
    if result is None:
        time.sleep(1)

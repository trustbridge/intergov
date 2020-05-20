from intergov.conf import env

MESSAGE_PATCH_API_ENDPOINT = env(
    'IGL_PROC_BCH_MESSAGE_API_ENDPOINT',
    default='http://message_api/message/{sender}:{sender_ref}'
)


MESSAGE_RX_API_ENDPOINT = env(
    'IGL_PROC_BCH_MESSAGE_RX_API_URL',
    default='http://message_rx_api/messages'
)

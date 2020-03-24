Message rx (reception) API
==========================

This is the API that receives messages from the intergov channels.
It is called by the channel infrastructure itself (not by applications). The
whole meaning of this API is to avoid blockchain listeners (who will notice
the new messages first) to do some implementation-specific actions (like sending
message to SQS), and just provide an universal and trivial API for them. It doesn't
work with any documents or binary data, just the small JSON message.

A component called a "per-channel blockchain event processor"
does something called "receive inbound blockchain event" (based on listening
blockchain events feed).
As part of doing this,
it posts a message (from the blockchain)
to this API.

This API supports a simple operation,

POST {message} /messages

Which is the same interface as used by the "Message API"
(see ../message_api/README) with one difference: sender_ref must be already present,
and the message status is not changed to "pending" because it's already received and has
no pending actions.

Errors
******
#. Unsupported Media Type Error => Generic HTTP Error => Unsupported Media Type
#. Message Data Empty Error
#. Message Deserialization Error
#. Message Validation Error
#. Message Absolute URL Error
#. Unable Write To Inbox Error
#. Generic HTTP Error
#. Internal Server Error

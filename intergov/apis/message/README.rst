Message API
===========

This is the API that allows users (by 'users' other services with some UI are meant)
to get the message by reference ID or post message to API inbox.

Typical users will be exporter app, importer app and so on.

Standard auth is required (actor should be entitled to view the message or send it
from given jurisdiction/etc).

Don't confuse it with message_rx_api, which is just another abstraction layer. This
one is a real API with auth, GET/POST endpoints and so on.


Endpoints
---------

Post message
************

    curl -XPOST http://127.0.0.1:5101/message \
        -H 'Content-type: application/json' \
        -d '{
            "sender": "AU",
            "receiver": "CN",
            "subject": "AU.abn0000000000.XXXX-XXXXX-XXXXX-XXXXXX",
            "obj": "QmQtYtUS7K1AdKjbuMsmPmPGDLaKL38M5HYwqxW9RKW49n",
            "predicate": "UN.CEFACT.Trade.CertificateOfOrigin.created"
        }'

As a result the same message dict will be returned but with new fields `status`: `pending` and `sender_ref`: some uuid.

Errors
******
#. Unsupported Media Type Error => Generic HTTP Error => Unsupported Media Type
#. Message Data Empty Error
#. Message Deserialization Error
#. Message Validation Error
#. Unable Write To Inbox Error
#. Generic HTTP Error
#. Internal Server Error


Get message by the reference
****************************

    curl -XGET http://127.0.0.1:5101/message/AU:1a0abd3b-2437-4c4a-95d0-a3fb39e530f6

As a result the full representation of the message will be returned. GET parameter is {sender}:{sender_ref},
where sender_ref is returned by the message POST endpoint.

Errors
******
#. Message Not Found Error => Generic HTTP Error => Not Found
#. Generic HTTP Error
#. Internal Server Error


Patch message metadata
**********************

    curl -XPATCH http://127.0.0.1:5101/message/AU:{sender_ref} \
         -d '{"status": "accepted"}'
         -H 'Content-Type: application/json'

As a result the full representation of the message will be returned. GET parameter is {sender}:{sender_ref},
where sender_ref is returned by the message POST endpoint.

Only supported metadata field now is "Status". WebSub notifications about
the status changes will be sent to all subscribers who is interested in it.

Errors
******
#. Message Not Found Error => Generic HTTP Error => Not Found
#. Generic HTTP Error
#. Internal Server Error

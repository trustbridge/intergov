Subscriptions API
=================

Interested parties to subscribe to some events using WebSub approach.

``docs/_build/html/intergov/repositories.html#subscriptions``

MVP is an object store repository that only supports the predicate__eq filter. (does not support predicate__wild or any non-predicate filters).

predicate__wild behavior can be simulated by clients, who makes multiple calls with different predicate__eq parameters. assuming partial predicate subscriptions are allowed.



Endpoints
---------

Endpoints are designed in accordance with WebSub standard.

The notification will arrive at the provided callback URL and will be POST JSON request
with message dict as content.


Register subscription
*********************

Send standard websub subscription request to `/subscriptions/`

It should be of x-form-urlencoded content type and of POST method.

    curl -XPOST http://127.0.0.1:5102/subscriptions \
         -d 'hub.callback=http://hostname.dn/websub/endpoint&hub.topic=UN.CEFACT.TRADE&hub.mode=subscribe'

Please note we don't require callback verification yet, so just after the subscription
is handles the notifications will start to be delivered.

UN topic may be xx.xx.xx.xx (minimum four parts) or xx.xx.xx.xx.xxd.xx (may be more)
or xx.xx.* or xx.xx.xx (both mean wildcard subscription on any topic first parts of which
are equal to provided)

Non-UN topics have the same validation rules except of no minimum of parts number. Example is
``message.status.change`` topic (or ``message.status.change.{sender_ref}.``)

A number of validation errors may be raised (for example, topics xx.yy* or xx..aa are invalid)

Deregister subscription
***********************

According the websub specification client just have to pass the same request, but mode parameter is `unsubscribe`.


Errors
******
#. Unsupported Media Type Error => Generic HTTP Error => Unsupported Media Type
#. Subscription Exists Error => Generic HTTP Error => Conflict
#. Subscription Not Found Error => Generic HTTP Error => Not Found
#. Unable To Post Subscription Error => Internal Server Error
#. Unknown Mode Error
#. Callback URL Validation Error
#. Topic Validation Error
#. Generic HTTP Error
#. Internal Server Error

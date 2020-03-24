Event Subsystem
===============

The event subsystem provides a mechanism
that allows 3rd parties to remain well informed
about the state of the system
without having to poll it.

It is entirely optional,
the system should work in a "fire and forget" manner.
This means that the B2G interactions
do not require further action
on behalf of the Business.
However, because the system operates with *eventual consistency*
and *best effort semantics*
(i.e. not *guaranteed delivery semantics*)
the event subststem may help applications
orchestrate their distributed processes.


Subscriptions API
-----------------

This is basically an implementation of WebSub
https://en.wikipedia.org/wiki/WebSub.
It allows Message API clients to discover
(be notified of) message changes without polling.

The implementation is `/intergov/apis/subscriptions_api`

The business logic is in these classes:

* SubscriptionDeregistrationUseCase
  (in `/intergov/use_cases/subscription_deregister.py`)
* SubscriptionRegisterUseCase
  (in `/intergov/use_cases/subscription_register.py`)

.. uml::

   @startuml
   component subscriptions_api
   usecase subscription_register [
      Register
      Subscription
   ]
   usecase subscription_deregister [
      De-Register
      Subscription
   ]
   database subscriptions [
      Subscriptions
   ]
   boundary post [
      post
      subscription
   ]
   boundary delete [
      delete
      subscription
   ]
   subscriptions_api -- subscription_deregister
   subscriptions_api -- subscription_register
   subscription_register -- post
   subscription_deregister -- delete
   post -- subscriptions
   delete -- subscriptions
   @enduml


Callbacks Spreader
^^^^^^^^^^^^^^^^^^

This is part of the WebSub infrastructure
that processes each event once.

.. autoclass:: intergov.processors.callbacks_spreader.CallbacksSpreaderProcessor

.. uml::

   component callback_spreader [
      Callbacks
      Spreader
   ]
   usecase uc_dispatch [
      Dispatch Message
      To Subscriber
   ]
   callback_spreader -- uc_dispatch
   database delivery_outbox [
      delivery
      outbox
   ]
   boundary post_job [
      post
      job
   ]
   uc_dispatch -- post_job
   post_job -- delivery_outbox
   
   database notifications [
      notifications
   ]
   boundary get_event [
      get
      event
   ]
   uc_dispatch -- get_event
   get_event -- notifications
   boundary delete_event [
      delete
      event
   ]
   uc_dispatch -- delete_event
   delete_event -- notifications
   
   database subscriptions [
      subscriptions
   ]
   boundary search_subscriptions [
      search
      subscriptions
   ]
   uc_dispatch -- search_subscriptions
   search_subscriptions -- subscriptions
   
.. autoclass:: intergov.use_cases.dispatch_message_to_subscribers.DispatchMessageToSubscribersUseCase


Callback Deliver
^^^^^^^^^^^^^^^^
This is the part of the WebSub infrastructure
that processes each message once
for every relevant subscriber.
It deffers to an external message queue
to implement best-effort delivery semantics.

.. autoclass:: intergov.processors.callback_deliver.CallbacksDeliveryProcessor

.. uml::

   @startuml
   component cbproc [
      Callbacks
      Delivery
      Processor
   ]
   usecase uc_deliver [
      Deliver
      Callback
   ]
   cbproc -- uc_deliver
   database delivery_outbox [
      delivery
      outbox
   ]
   boundary get_job [
      get
      job
   ]
   uc_deliver -- get_job
   get_job -- delivery_outbox
   boundary delete_job [
      delete
      job
   ]
   uc_deliver -- delete_job
   delete_job -- delivery_outbox
   boundary post [
      POST
   ]
   uc_deliver -- post
   cloud subscriber
   post -- subscriber
   @enduml

.. autoclass:: intergov.use_cases.deliver_callback.DeliverCallbackUseCase

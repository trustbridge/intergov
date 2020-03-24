Platform Services
=================

These components are involved in message processing
regardless of the origin or destination of the message.


Inbound Message Processor
-------------------------

This worker processes new messages
regardless of if they came from a B2G route
(i.e. Public Message API)
or a G2G route
(i.e. from a G2G Channel).

The code in */intergov/processors/message_processor/*
instantiates and runs an **InboundMessageProcessor**.

.. autoclass:: intergov.processors.message_processor.InboundMessageProcessor

.. uml::

   @startuml
   component imp [
      Inbound
      Message
      Processor
   ]
   usecase pmuc [
      Process
      Message
   ]
   imp -- pmuc
   boundary post_message_lake [
      post
      message
   ]
   pmuc -- post_message_lake
   database message_lake [
      message
      lake
   ]
   post_message_lake -- message_lake
   
   boundary post_message_acl [
      post
      message
   ]
   pmuc -- post_message_acl
   database object_acl_repo [
      object
      ACL
   ]
   post_message_acl -- object_acl_repo
   
   boundary post_message_channel_inbox [
      post
      message
   ]
   pmuc -- post_message_channel_inbox
   database bc_inbox_repo [
      channel
      inbox
   ]
   post_message_channel_inbox -- bc_inbox_repo
   
   
   boundary post_job_orr [
      post
      job
   ]
   pmuc -- post_job_orr
   database object_retreval_repo [
      object
      retreval
   ]
   post_job_orr -- object_retreval_repo
   
   boundary post_message_notifications [
      post
      message
   ]
   pmuc -- post_message_notifications
   database notifications_repo [
      notifications
   ]
   post_message_notifications -- notifications_repo

   boundary post_channel_outbox [
      post
      message
   ]
   pmuc -- post_channel_outbox
   database blockchain_outbox [
      channel
      outbox
   ]
   post_channel_outbox -- blockchain_outbox
   @enduml

.. autoclass:: intergov.use_cases.ProcessMessageUseCase

The message processing task touches quire a few backing services.


Message Updater
---------------
This worker updates the metadata of existing messages,
regardless of the source of the change.

Rather than updating messages directly,
other workers dispatch a "message update job"
to a queue, and this worker then performs the deed
in the message lake
(using a patch call on the message API).

.. autoclass:: intergov.processors.message_updater.MessageUpdater

.. uml::

   @startuml
   component mu [
      Message
      Updater
   ]
   component patch_endpoint [
      Message
      API
   ]
   usecase uc [
      Update Message
   ]
   mu -- uc
   uc -- patch_endpoint
   database repo [
      message
      updates
   ]
   boundary get [
      get
      job
   ]
   get -- repo
   uc -- get
   boundary delete [
      delete
      job
   ]
   uc -- delete
   delete -- repo
   boundary update [
      increment
      retry
      counter
   ]
   uc -- update
   update -- repo
   @enduml


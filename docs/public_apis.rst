Public Interfaces
=================

These are the interfaces (REST APIs)
that are used for B2G interactions.

They map to the description on
https://edi3.org/specs/edi3-icl/master/#architecture-overview

Note there is also a generic
(general purpose)
events subscription API
that is also public.
It is documented in
the chapter following this one,
as part of the event subsystem.


General Message API
-------------------

This component provides the main API
used by members of the regulated community
to send messages to the Government,
which may or may not be forwarded to other Governments
(depending on intergovernment channels,
and the policy of the regulator, etc).

It is also used to check the status of messages
(e.g. have they been delivered to foreign governments yet?),
and to update the status of messages.

The implementation is */intergov/apis/message_api/*

The specific business logic is in these classes:

* GetMessageBySenderRefUseCase
  (in `/intergov/use_cases/get_message_by_sender_ref.py`)
* PatchMessageMettadataUseCase
  (in `/intergov/use_cases/patch_message_metadata.py`)
* EnqueueMessageUseCase (in `/intergov/use_cases/enqueue_message.py`),
  which is the same business logic as in the Message Receiving API.

.. uml::

   @startuml
   component message_api [
      Public
      Message
      API
   ]
   usecase get_message_by_sender_ref [
      Get Message
      by sender_ref
   ]
   usecase patch_message_metadata [
      Patch
      Message
      Mettadata
   ]
   usecase enqueue_message [
      Enqueue
      Message
   ]
   boundary get [
      get
      message
   ]
   boundary update_metadata [
      update
      metadata
   ]
   boundary post [
      post
      message
   ]
   boundary post_job [
      post
      job
   ]
   database message_lake [
      message
      lake
   ]
   database bc_inbox [
      bc
      inbox
   ]
   database notification_repo [
      notifications
   ]
   message_api -- get_message_by_sender_ref
   message_api -- patch_message_metadata
   message_api -- enqueue_message
   enqueue_message -- post
   post -- bc_inbox
   get_message_by_sender_ref -- get
   get -- message_lake
   patch_message_metadata -- get
   patch_message_metadata -- update_metadata
   patch_message_metadata -- post_job
   post_job -- notification_repo
   update_metadata -- message_lake
   @enduml


Document API
------------

This is how people save and access documents,
which are the subject of G2G messages.

The implementation is `/intergov/apis/document_api.py`
and the logic is in the
AuthenticatedObjectAccessUseCase
(in `/intergov/use_cases/authenticated_object_access.py`)
and StoreObjectUseCase
(in `/intergov/use_cases/store_object.py`)

.. uml::

   @startuml
   component document_api
   database object_lake [
      object
      lake
   ]
   database object_acl [
      object
      ACL
   ]
   boundary get_body [
      get
      body
   ]
   boundary search [
      search
   ]
   usecase authenticated_object_access [
      Authenticated
      Object
      Access
   ]
   usecase store_objects [
      Store
      Objects
   ]
   boundary post_from_file_obj [
      post
      file
   ]
   boundary allow_access_to [
      allow
      access
   ]
   document_api -- authenticated_object_access
   authenticated_object_access -- get_body
   get_body -- object_lake
   authenticated_object_access -- search
   search -- object_acl
   document_api -- store_objects
   store_objects -- allow_access_to
   allow_access_to -- object_acl
   store_objects -- post_from_file_obj
   post_from_file_obj -- object_lake
   @enduml


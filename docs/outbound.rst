Outbound Message Flow
=====================

These components are involved in the flow of messages
from one Government to another.
Specifically, the sending side of the equation.



Multichannel Router
^^^^^^^^^^^^^^^^^^^
This is a core component.
It is responsible for routing messages between Governments
(using the appropriate channel).

.. autoclass:: intergov.processors.blockchain_router.MultiChannelBlockchainWorker

Note: channels abstract over topology, technology and wire protocols.
This means that countries are free
to determine bilaterally or multilaterally
agreeable channels.
This component will be configured to use the channels
as per the operating countries agreements.

.. uml::

   @startuml
   component router [
      Multi-Channel
      Router
   ]
   usecase uc [
      Route To
      Channel
   ]
   router -- uc
   queue ch1 [
      channel 1
   ]
   queue ch2 [
      channel 2
   ]
   queue chx [
      channel ...
   ]
   boundary rt [
      routing
      table
   ]
   uc -- rt
   rt -- ch1
   rt -- ch2
   rt -- chx
   database outbox [
      delivery
      outbox
   ]
   boundary outbox_patch [
      patch
      message
   ]
   outbox_patch -- outbox
   router -- outbox_patch
   boundary outbox_get [
      get
      message
   ]
   router -- outbox_get
   outbox_get -- outbox
   boundary post_pcm [
      post
      job
   ]
   router -- post_pcm
   database pcm_repo [
      channel
      pending
   ]
   post_pcm -- pcm_repo
   boundary push_mu [
      patch
   ]
   router -- push_mu
   database mu_repo [
      delivery
      status
   ]
   push_mu -- mu_repo
   @enduml

.. autoclass:: intergov.use_cases.route_to_channel.RouteToChannelUseCase

.. TODO: refactor the rest of the logic into another use-case
   rather than having it 
	       
This process needs to be slightly more complicated
than it might seem at first.
Channels need to be potentially asynchronous.
For example, with a blockchain channel,
messages are "written" to the extent of the consensus.
It's technically possible for blockchains to fork,
meaning that the concensus "changes it's mind"
about the shared view of history.

This means that,
in addition to routing the message to the channel,
the router must also dispatch a couple of jobs
(asynchronous processing tasks):

* "Channel Pending" jobs are used keep track of messages
  that may not yet have been sucessfully delivered by the channel.
  Depending on the outcome of channel processing,
  the appropriate steps for processing these messages
  may not yet be known.
* "Delivery Status" journal is updated
  to keep track of the channel delivery status
  so stakeholder processes can remain appraised
  of important delivery/non-delivery events.


Channel Poller
^^^^^^^^^^^^^^

Not to be confused with the Channel Observer:
This worker checks on the status of messages
that have been sent to a channel BY US
(the other one discovers new messages
that have been sent on a channel TO US).

.. autoclass:: intergov.processors.channel_poller.ChannelPollerWorker

.. uml::

   @startuml
   component worker [
      Channel
      Poller
   ]
   usecase uc [
      Check Status of
      Pending Deliveries
   ]
   worker -- uc
   queue channel
   database pending [
      pending
      deliveries
   ]
   boundary check [
      check
      status
   ]
   uc -- check
   check -- channel
   boundary get [
      get
   ]
   uc -- get
   get -- pending
   boundary del [
      delete
   ]
   uc --del
   del -- pending
   database updates [
      message
      updates
   ]
   boundary post [
      post
      job
   ]
   uc -- post
   post -- updates
   @enduml

This worker deletes jobs from the "pending messages" queue
when an change is detected (by polling the channel).
If no change is detected,
the job is not deleted from the pending messages queue.
But neither is it returned to the queue -
the worker holds a lock on the job until it goes stale.
This way, the worker polls the queue sequentially
at most once per task timeout period configured on the queue.

It's a bit of a cheap trick but it seems to work quite well.


Rejected Message Processor
^^^^^^^^^^^^^^^^^^^^^^^^^^
When the multi channel router tries to send a message to a channel,
there are various reasons why the attempt might fail.
Because the process is asynchronous,
the sending component (multi channel router)
does not wait to know the status,
it just carries on sending.

That is why the channel poller component
manages data in the "pending deliveries" database
and posts update jobs to the "message updates" queue.
Thus, message updates queue contains jobs to be done
updating the delivery status of messages.

The task of this component
(rejected message processor)
is to process those jobs.

.. autoclass:: intergov.processors.rejected_status_updater.RejectedStatusUpdater

.. uml::

   @startuml
   component rsu [
      Rejected
      Message
      Processor
   ]
   usecase uc [
      Process
      Rejected
      Message
   ]
   rsu -- uc
   boundary umd [
      update
      metadata
   ]
   uc -- umd
   database ml [
      message
      lake
   ]
   umd -- ml
   boundary get [
      get
   ]
   uc -- get
   boundary delete [
      delete
   ]
   uc -- delete
   database rm [
      rejected
      messages
   ]
   get -- rm
   delete -- rm
   @enduml


.. autoclass:: intergov.use_cases.reject_pending_message.RejectPendingMessageUseCase


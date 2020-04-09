Multi-Channel Architecture
==========================

This page explains the advantages
of a multi-channel architecture
facilitating cross-border trade
by enabling Government to Government (G2G)
document exchange.


Hubs models are obvious, but possibly wrong
-------------------------------------------

First, let's start
by considering the alternative
to multi-channel architecture;
a single channel (or "Hub") model.

.. uml::

   @startuml
   component ca [
      Country A
   ]
   component cb [
      Country B
   ]
   component cc [
      Country C
   ]
   component cd [
      Country D
   ]
   component ce [
      Country E
   ]
   component cf [
      Country F
   ]
   component cg [
      Country G
   ]
   component ch [
      Country ...
   ]
   queue Hub
   ca -- Hub
   cb -- Hub
   cc -- Hub
   cd -- Hub
   Hub -- ce
   Hub -- cf
   Hub -- cg
   Hub -- ch
   @enduml

In this model, there is a single logical Hub
that all messages pass through.
This logical Hub could be a distributed ledger,
traditional database, paper clearinghouse,
so some other technology.
The basic idea is that countries
send their messages to this hub
and receive their messages from it too.

Hub models require participants
to adopt a common technology platform.
This platform must meet the needs
of all participants
both in the moment and in the future.

Hub architectures have been built many times before.
Some people find this sort of design intuitively appealing,
perhaps because the idea of standardising on a single solution
seems like it should minimise interoperability challenges.

But standardising on a single implementation
solves interoperability the wrong way.
Interoperability comes from standard interfaces,
not from common implementation.
If two systems have an effective way to interoperate,
then there is no reason
for them to have the same implementation.
Individual participants should be free
to implement their parts of the system
in the way that makes the most sense to them.


What is a multi-channel architecture?
-------------------------------------

As an alternative to the Hub model,
consider the following:

.. uml::

   @startuml
   component ca [
      Country A
   ]
   component cb [
      Country B
   ]
   component cc [
      Country C
   ]
   component cd [
      Country D
   ]
   component ce [
      Country E
   ]
   component cf [
      Country F
   ]
   component cg [
      Country G
   ]
   component ch [
      Country ...
   ]
   queue ch1 [
      bilateral
      general purpose
   ]
   queue ch2 [
      multilateral
      topic-specific
   ]
   queue ch3 [
      bilateral
      topic specific
   ]
   queue ch4 [
      multilateral
      general purpose
   ]
   queue ch5 [
      multilateral
      general purpose
   ]
   cb -- ch5
   cc -- ch5
   cd -- ch5
   ch5 -- cf
   ch5 -- cg
   ch5 -- ch
   ca -- ch1
   ca -- ch2
   cb -- ch2
   cb -- ch4
   cc -- ch2
   cd -- ch3
   ch1 -- ce
   ch4 -- ce
   ch2 -- cf
   ch4 -- cf
   ch2 -- cg
   ch3 -- ch
   @enduml

The above illustration shows a multi-channel scenario where:

* Country A and Country E have a bilateral arrangement for exchanging messages on any topic
* There is a multilateral arrangement
  between Countries B, E and F
  that supports messages on any topic
* There is a multilateral arrangement
  between Countries A, B, C, F and G
  that supports messages on a specific topic
* There is a multilateral arrangement
  between Countries B, C, D, F, G and others (...)
  that supports messages on any topic
* There is an arrangement between Country D and others
  supporting messages on some specific topic.

On first impression, the above scenario
might seem overcomplicated.
However, the reality of international trade
is vastly more complex than this diagram!

There three distinct reasons
why a multi-channel architecture is necessary.


Support for Variable Topology
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Agreements between Countries are inherently bespoke.
Some are bilateral (links),
others are multilateral (networks).
The scope and details are customised
and optimised through a process of negotiation.
They changes over time,
as existing arrangements are refined or adjusted
and new arrangements are made.

Even if a hub model is theoretically better
(no such theory is offered here),
the idea of asking almost 200 countries
to agree on a precise scope and details
for sharing cross-border trade documents
seems like it would be slow,
difficult and unlikely to succeed.

There are examples of universal hubs,
but they have narrow scope
(for example, ePhyto Certification).

It seems more pragmatic to assume that
cooperative sharing arrangements
involving cross-border trade documentation
will involve a similar process of negotiation
to other international agreements.

While technical standardisation may reduce waste,
free countries will always ultimately determine
who they share what with, when and how;
and those arrangements will change over time
with policy and circumstance.

Any design that does not support variable topologies
seems likely to result in a sub-optimal compromise.


Support for Variable Technology
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Technical solutions for cross-border
document exchange have existed for many centuries.
Emerging technologies
(such as distributed ledgers)
have different characteristics
which may confer some advantages,
make new things possible
or make previously difficult things more easy.
No doubt technology will continue to evolve
and as-yet unimagined solutions will emerge
with even more favourable characteristics.

Sometimes, the best technology choice in a given situation
would not be the best choice in a different situation.
The asset lifecycle of existing systems,
infrastructure, organisational capacities
and technology strategies of different groups
can create a prediliction
(or an aversion)
for specific technologies.

Even if it were possible to determine
a universal "best technology"
to implement cross-border trade document sharing,
that would be a fleeting anomaly.

Any design that does not allow countries
to negotiate technology choices
(and mutually agree to update or upgrade technology)
seems incongruent with
the other negotiated details
of international arrangements.
An attempt to unilaterally impose
a single, unchanging technology choice
would not only require impractically challenging negotiation,
it would also pit the fate of the system
against the march of technological progress.


Support for Variable Protocols
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The current proof of concept
supports a wire protocol that
we called "Discrete Generic Message" (DGM).
Each communication packet between countries
contains a single ("discrete") message,
and there is no limit to
the taxonomy of message types
that could be sent
(generic).

This protocol was adequate and sufficient
for the first stage of our Proof Of Concept.
It may yet prove to be a useful protocol
in a wide range of situations.
However, there are also situations
where a different protocol design
may be more appropriate.

If there are very high message volumes,
or a technology is used with a low bandwidth
(or high cost per transmission),
then a *batched* protocol design
may be more appropriate.
Rather than sending "discrete" messages
(one at a time)
a batch protocol could send
a compressed collection of messages
in in each packet.
This would involve trade-offs,
especially with all-or-nothing validation semantics
(such as blockchain consensus),
but there may be situations where
a batch protocol is the most practical choice.

.. non-generic messages, legacy fascades
.. ...and/or smart contracts, rich validation and guard conditions

Some distributed ledger technologies
support a feature called "Smart Contracts".
These are sometimes known by other names,
such as "Transaction Families" or "Chain Code",
but what they all have in common is that they allow
the channel to enforce mutually agreed policies
in a trustworthy way.
Smart contracts allow distributed ledger
to operate like an "independant umpire",
which is potentially useful
in a wide variety situations
that require adversarial trust.
However, this has the downside
of tightly coupling policies
to the message transport mechanism.
This means the channel can only be used
for the purposes that correspond exactly
to the policies implemented in the smart contract.

Given the bespoke nature of international trade agreements,
developing a channel that fits them all well
could be very difficult or perhaps impossible.
The strategy of allowing multiple channels
might make the solution seem more complicated
from some perspectives,
but if countries can route messages over multiple channels
then it should be possible for a country
to maintain integration with the collection of channels
that best fit their needs.


Interoperability requires standard interfaces
---------------------------------------------

The multi-channel architecture theory needs to be tested.

This Proof of Concept software includes a "channel router" component,
with a mechanism for deciding which channel should be used for each message
(i.e. an "outbound message routing" mechanism).
It also includes a "channel observer" component,
which is a mechanism for accepting messages from different messages
and funneling them all into the same process regardless of how they are transmitted.

The code is designed in a way that assumes
that a standardised "Channel API" exists,
however an actual Channel API
has not been developed yet.

This requires active research,
which would benefit greatly from integrating
one (or preferably more) existing G2G message channels.

If a standard Channel API is developed
that can successfully be applied to existing G2G message channels,
then it should be possible
to provide an abstraction over the existing channels
such that:

* Business to Government (B2G) transactions
  operate against standard APIs,
  which hide the details of which actual channel is used.
* Governments should be able to modify their channel implementations
  in way that insulates their regulated community from the change.
  In other words, without impacting their users.
* Makes it possible to integrate
  additional, new channels
  without modifying the standard Channel API design.


WIP
---
**Membership of a channel**

CHAFTA:

Under what conditions can a country join a channel?

 - AU gives CN the keys to use the channel out-of-bounds
 - CN is given access to a document by combination of a key (identifying them as CN) and because we sent a message to CN which caused the ACL to be updated

Does the routing need to be more fine grained than a country?

 - Jurisdiction




**Structuring the doco**

Integrator doc
 - messages API
 - document API
 - subscription API
 - auth + access control

Channel developer doc
 - channel API
 - subscription API?

Node developers guide
 - System components:
   + internal microservices
     * message rx api - callback
     * channel api
   + worker components
   + repos...
 - code structure (clean architecture doc)
   + use cases + requests + response objects
     * doco of tests included
   + domain model + serialization
 - diagrams, overview stuff


**Messaging between countries**

.. uml::

Node is a message router. Technical ACK - I got the message and I downloaded the documents.

Sender: AU
Receiver: CN
Subject: ID of object
Object: the document
Predicate: states of the object


   @startuml
   start
   :AU sends message with COO to CN - subject: aig.com.au:<AIG_ID>, predicate: unece.un.org:coo:created;
   :CN technical ACKs - subject: , predicate: unece.un.org:technicalAck:received/downloaded/etc...;
   stop
   @enduml


If the subject of the ack is the hash of the canonically formatted <from to subject object predicate>, then we can use the same protocol for side trees and their leaves?

Sender: CN
Receiver: AU
Subject: cn.gov:<hash>
Object: None
Predicate: unece.un.org:technicalAck:objectDownloaded

Don't technical ack an object of None OR don't technicalAck a technicalAck predicate


The node may deduplicate messages; two scenarios:
 - the exact same message is sent twice, for no good reason
 - the same message is sent again because the receiver told us that it could not get the first one


**TODO:**

 - define IDs for messages and documents and their contexts
 - List an example set of documents that might be sent


**Node message state:**

POST /messages/

returns <id> aka ``sender_ref``

GET /messages/<id>

GET /messages/<id>/status

GET /messages/<id>/journal


.. uml::

   @startuml
   [*] --> Pending
   Pending : either posted to the channel or\n waiting to be bundled with other messages
   Pending --> Sent : Sent to the channel\n as a single message
   Pending --> Bundled
   Pending --> Failed : If the message cannot be\nsent (pre-channel fail)
   Bundled --> Sent
   Bundled : A "bundler" (perhaps the router) groups messages,\n puts them into a document and\n sends a message with that document as the object.
   Bundled : If the bundled message fails, we think the messages\n should be set back to pending\n and can be bundled as appropriate at the time.
   Sent --> Delivered
   Sent : We have successfully asked the\n channel to deliver the message. Delivery is async.
   Sent --> Pending : If the message was not\nsuccessfully delivered,\nit must be tried again
   Sent --> Failed : If the message cannot be delivered\nafter trying again (channel fail)
   Delivered : The channel reports that\n delivery has been successful.
   Delivered -[dashed]-> [*] : Semi-terminal\nSuccess is a zombie,\nonly failure is permanent
   Delivered -up-> Withdrawn
   Withdrawn : The message was thought to be delivered\n but that was in error.\nUnlikely, but necessary due to\nthe vagaries of blockchain.
   Withdrawn --> Pending
   Failed --> [*]
   @enduml

/messages/<id>/acknowledgement

.. uml::

   @startuml
   [*] --> Unacknowledged
   Unacknowledged --> TechnicalAck
   Unacknowledged --> TechnicalNack
   TechnicalAck --> [*]
   TechnicalNack --> [*]
   @enduml


Bundled messages would be put into a "message list" document and the "bundle message" is a message about a document that is a list of messages, not a message about a single document.

Blockchain problems that we are trying to deal with:

 - If the message is put on the chain but we don't consider it delivered and China download the document and ack it anyway, it may end up being on a fork and not ever sent.


**Message reception state:**

.. uml::

   @startuml
   [*] --> Unacknowledged
   Unacknowledged --> TechnicalAck
   Unacknowledged --> TechnicalNack
   TechnicalAck --> [*]
   TechnicalNack --> [*]
   @enduml


Channel Technical Details
-------------------------

A channel consists of a posting API and a receiving API on one end, a channel medium in the middle and one or more posting and receiving APIs on the other ends.
 - Posting to a channel is a broadcast mechanism; receivers need to determine if a message is meant for them or not
 - Sender verification is the responsibility of the receiver
 - Non-repudiation may be guaranteed by the channel medium

.. uml::

   @startuml
   title A channel
   
   cloud "Channel Medium" as cm
   
   package "Channel API - side A" {
       [Channel Posting API] as a_cpa
       (post message) as a_pm
       [Channel Receiving API] as a_cra
       (receive message) as a_rm

       a_cpa --> a_pm
       a_pm --> cm
       a_cra <-- a_rm
       a_rm <-- cm
   }
   
   package "Channel API - side B" {
       [Channel Posting API] as b_cpa
       (post message) as b_pm
       [Channel Receiving API] as b_cra
       (receive message) as b_rm

       b_cpa --> b_pm
       b_pm --> cm
       b_cra <-- b_rm
       b_rm <-- cm
   }
   @enduml



**Channel message state:**

 - Channel encrypts and decrypts messages if required (ie. if the channel medium is public)
 - Channel requires auth at each end to restrict access to messages
   + Therefore, each channel knows which nodes are allowed to read and post messages

.. uml::

   @startuml
   title Send message across channel with auth
   hide footbox
   
   box "Local Node" #LightGreen
       participant Node
       participant Channel_Posting_API
   end box
   participant Channel_Medium
   box "Foreign Node" #LightBlue
       participant Channel_Receiving_API
       participant Foreign_Node_1
   end box
   participant Foreign_Node_2
   participant Foreign_Node_3
   
   Node->Channel_Posting_API: post message
   note right: authorise sender and encrypt message with channel key pair
   Channel_Posting_API->Channel_Medium: write message
   Channel_Receiving_API->Channel_Medium: get new messages
   note right: decrypt message
   Channel_Receiving_API->Foreign_Node_1: notify message ready
   Channel_Receiving_API->Foreign_Node_2: notify message ready
   Channel_Receiving_API->Foreign_Node_3: notify message ready
   Foreign_Node_1->Channel_Receiving_API: authenticate and request message
   Foreign_Node_2->Channel_Receiving_API: authenticate and request message
   @enduml

.. uml::

   @startuml
   title Sending message back across same channel medium
   hide footbox
   
   box "Local Node" #LightGreen
       participant Node
       participant Node_Other
       participant Channel_Receiving_API_Foreign
   end box
   participant Channel_Medium
   box "Foreign Node" #LightBlue
       participant Channel_Posting_API_Foreign
       participant Foreign_Node
   end box

   Foreign_Node->Channel_Posting_API_Foreign: post message
   Channel_Posting_API_Foreign->Channel_Medium: write message
   Channel_Receiving_API_Foreign->Channel_Medium: get new messages
   Channel_Receiving_API_Foreign->Node: notify message ready
   Channel_Receiving_API_Foreign->Node_Other: notify message ready
   Node->Channel_Receiving_API_Foreign: authenticate and request message
   Node_Other->Channel_Receiving_API_Foreign: authenticate and request message
   @enduml

.. uml::

   @startuml
   title Send Technical Ack back
   hide footbox
   
   participant Node
   participant Node_Other
   participant Channel
   participant Foreign_Node

   Foreign_Node->Channel: encrypt with Technical Ack key pair and post message
   Node->Channel: get message
   note right of Node: Node decrypts the Technical Ack and trusts it because it was encrypted with the accepted key pair
   Node_Other->Channel: get message
   note right of Node_Other: Node_Other attempts to decrypt the Technical Ack but it has a different key pair so decryption fails
   @enduml

Could a channel be a single direction? Ie. Channel Posting API, Channel Receiving API
If we want to go both ways, we just duplicate the APIs in the other direction. They can even share secrets to allow them to post on the same channel medium.
Ie. key-pair for posting AU->CN and different key-pair for posting CN->AU. key-pairs are unique to pair of countries, direction and channel. This allows AU to post messages to CN but not read (the content of) those messages. So, no

We don't need a specific channel for Acks, we just need to authorise SOMEONE to send Acks. Messages with Acks that aren't authorised for that predicate are ignored/recorded as invalid.
Real world - who can ack a CoO? We don't care, but we give China the key-pair that allows someone to and then it's China's problem to assign/move that assignment around.

Same for Acks as for message key-pairs.

Router translates Receiver (Jurisdiction=AU/CN) and Predicate to a Participant on a Channel. Sender turns into Participant on a Channel.


POST /messages

GET /messages/<id>

GET /messages/<id>/status

.. uml::

   @startuml
   [*] --> Received
   Received --> Confirmed
   Confirmed : Means that the message has passed through the channel.\nOn a blockchain, this means that there are sufficient blocks on top.\nOn an RDS this means that the message was commit to the table.\nEffectively the end state for most successful messages.
   Received --> Undeliverable
   Undeliverable : The channel was unable to write the message\nand has stopped trying to confirm
   Confirmed --> Revoked
   Revoked : Confirmation was erroneously issued on a fork.\nWe expect this to be extremely rare; \nit is a theoretical possibility.
   Revoked --> [*]
   Undeliverable --> [*]
   @enduml

BlockchainChannel:

 - received message and writes to an RDS, returning an ID
 - writes to the blockchain
 - waits (forever; stays in Received) and observes until:

   + multiple blocks are written on top of the chain (Confirmed)
   + OR observes that it was on a fork and the chain has moved from a previous block and the message was never written (Undeliverable)

It is the channel API's business to decide if it fails as Undeliverable on the first attempt, or whether it tries a few times (config value) before being marked as Undeliverable.


GET/POST /<subscription endpoints> - WEBSUB standard

GET /messages/?sent_date=2020-01-12Z123456&receiver=AU - or do we need to use a delivered_date? How do we handle the uncertainty of a block not being added to the chain after it's been sent?


**Channel API**

.. uml::

   @startuml
   title Channel API
   
   participant Node
   participant Channel_API
   participant Channel
   participant Channel_API_2
   participant Node2
   
   
   Node->Channel_API: get nodes
   Node->Channel_API: put nodes/<Node> (document API endpoints, ssl pubkey)
   
   ... Some ~~long delay~~ ...
   
   Node->Channel_API: subscribe to new messages for me (AU)
   Node2->Channel_API_2: subscribe to new messages for me (CN)
   
   ... Some ~~long delay~~ ...
   
   Node->Channel_API: send message (A)
   Node->Channel_API: get message status
   Node->Channel_API: get message status
   Node->Channel_API: get message status
   
   Channel_API->Channel: send message (A)
   Node->Channel_API: get message status (SENT)
   
   Channel->Channel_API_2: send message (A)
   
   Channel_API_2->Node2: new message (A) received
   
   ... Some ~~long delay~~ ...
   
   Node2->Channel_API_2: send message (B)
   Channel_API_2->Channel: send message (B)
   Channel->Channel_API: send message (B)
   
   Node<-Channel_API: new message (B) received
   @enduml



**Foreign Document Access (incomplete)**

.. uml::

   @startuml
   title Foreign document access
   
   participant Chamber
   box "Local Node" #LightGreen
       participant Documents_API
       participant Messages_API
   end box
   box "Channel" #LightOrange
       participant Channel_API
       participant Channel
       participant Foreign_Channel_API
   end box
   box "Foreign Node" #LightBlue
       participant ForeignNode
   end box
   
   
   Chamber->Documents_API: publish document
   activate Documents_API
   return multihash
   
   Chamber->Messages_API: send message
   activate Messages_API
   return sender_ref
   
   Messages_API->Channel_API: send message
   Channel_API->Channel_API: send message
   
   ... Some time later ...
   
   Messages_API<-Channel_API: message sent
   Messages_API->Documents_API: update ACL for document\nfrom message
   
   ... Some time later ...
   
   ForeignNode->Documents_API: get document
   activate Documents_API
   return document
   
   ForeignNode->Foreign_Channel_API: send technical ack
   @enduml



**Intergov Node**

.. uml::

   @startuml
   title Intergov node
   
   package "Documents API" {
       [Document API] -down-> (publish document)
       [Document API] -down-> (get document)
       (publish document) -down-> [Document Lake]
       (get document) -down-> [Document Lake]
       (get document) -down-> [Document ACL]
       (retrieve and store\foreign docs) -up-> [Document Lake]
       [<<docker>> document spider] -up-> (retrieve and store\foreign docs)
       (retrieve and store\foreign docs) -down-> [foreign object proxy]
   }
   
   package "Messages API" {
       database Message_Lake
       [Message API] -down-> (get message by id)
           (get message by id) -down-> Message_Lake
       [Message API] -down-> (post message)
           (post message) -down-> [Message Inbox]
       [Message Inbox] <- (poll for new messages)
           (poll for new messages) -> [Message Router]
       [Message Router] -down-> Channel
       [<<docker>>\nrejected\nstatus\nupdater] -up-> (update status of rejected messages)
       (update status of rejected messages) -up-> Message_Lake
   }
   
   package "Subscriptions" {
       database Subscriptions_S3
       [Subscriptions API] -down-> (register subscription)
           (register subscription) -down-> Subscriptions_S3
       [Subscriptions API] -down-> (deregister subscription)
           (deregister subscription) -down-> Subscriptions_S3
       [Message Listener] -up-> Subscriptions_S3
       [Message Listener] -> [Channel API]
       [<<docker>>\noutbound\ncallback\nprocessor] -up-> (dispatch callbacks to subscribers)
           (dispatch callbacks to subscribers) -up-> Subscriptions_S3
           (dispatch callbacks to subscribers) -up-> Publish_outbox
           (dispatch callbacks to subscribers) -up-> Delivery_outbox
       (deliver callback) -down-> Delivery_outbox
       (deliver callback) -up-> [callback proxy]
       [<<docker>> callback deliverer] -down-> (deliver callback)
       [callback proxy] -up-> (receive callback)
   }
   
   package "Channel" {
       [Channel API] -> [Channel]
   }
   @enduml

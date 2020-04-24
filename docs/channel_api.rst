Channel API
===========

A node may use multiple channel implementations, therefore we have decoupled the node from the channel by defining this channel API. The reasons behind this are documented in the design note on :doc:`multichannel architectures <architecture_decision_notes/multichannel_architecture>`.

A channel consists of two or more endpoints and a shared medium in the middle - eg. blockchain.

An endpoint consists of two parts, either of which are optional, but the endpoint is only useful if at least one part is implemented.

 - The Posting API - A node uses this to send a message through a channel
 - The Receiving API - A node uses this to receive messages addressed to its jurisdiction [#]_ from a channel

These two APIs handle the complexities of the channel medium and are authorised to send messages on the channel (on behalf of an entity). Therefore, access to these APIs must be controlled.

.. uml::

   @startuml
   caption A channel with channel APIs and a channel medium
   
   cloud "Channel Medium" as cm
   
   package "Channel API - endpoint A" as a_endpoint {
       [Channel Posting API] as a_cpa
       (post message) as a_pm
       [Channel Receiving API] as a_cra
       (receive message) as a_rm
   }

   package "Channel API - endpoint B" as b_endpoint {
       [Channel Posting API] as b_cpa
       (post message) as b_pm
       [Channel Receiving API] as b_cra
       (receive message) as b_rm
   }

   package "Channel API - endpoint C\n(posting only)" as c_endpoint {
       [Channel Posting API] as c_cpa
       (post message) as c_pm
   }

   package "Channel API - endpoint D\n(receiving only)" as d_endpoint {
       [Channel Receiving API] as d_cra
       (receive message) as d_rm
   }

   a_cpa --> a_pm
   a_pm --> cm
   a_cra <-- a_rm
   a_rm <-- cm

   b_cpa --> b_pm
   b_pm --> cm
   b_cra <-- b_rm
   b_rm <-- cm

   c_cpa -right-> c_pm
   c_pm -up-> cm

   d_cra <-left- d_rm
   d_rm <-up- cm

   @enduml


.. [#] Nodes act on behalf of jurisdictions, which is why it's not addressed to the node, but the jurisdiction. If there are multiple nodes in a jurisdiction subscribed to a particular channel, all of those nodes will receive all messages addressed to that jurisdiction.



**Channel Auth**

A channel posting endpoint is posting messages AS the jurisdiction and therefore must ensure that only nodes that are permitted to send messages AS the jurisdiction are allowed to post.

It is the channel endpoint operator's business to determine access requirements for the channel.

For example, if a node operator is operating private channel APIs for its own use, and not allowing any other nodes to use their channel APIs, then network level security may be sufficient. Similarly, a developer may use docker networking connections to restrict access without implementing any explicit access controls. However, if a channel operator wanted to support multiple nodes, then they would need to develop a satisfactory access control regime, sufficient for the requirements of that channel.

A channel may have many nodes using it, but tens not 1000s.

The current reference implementation at TODO assumes that the node operator is also the channel endpoint operator, therefore manual devops style auth configuration is fine (eg. subnet only networking/whitelisting IP addresses/API Gateway SIG4 certs etc...).

Notes:

 - Posting to a channel is a broadcast mechanism; receivers need to determine if a message is meant for them or not
 - Sender authorisation is implemented by the channel
 - Sender verification is the responsibility of the receiver
 - Non-repudiation may be guaranteed by the channel medium

Question: Is posting to a channel always broadcast? Or may some channel mediums deliver only to the intended recipient?
And are the above statements all true?


Channel Posting API
-------------------

| ``POST /messages``
| ``GET /messages/<id>``
| ``GET /messages/<id>?fields=status``

.. uml::

   @startuml
   caption Posting a message to a channel
   hide footbox
   
   box "Local Node" #LightGreen
       participant Message_API
       participant Channel_Posting_API
   end box
   participant Channel_Medium
   box "Foreign Node" #LightBlue
       participant Foreign_Node
   end box
   
   Message_API->Channel_Posting_API: post message
   activate Channel_Posting_API
   return id

   Channel_Posting_API->Channel_Medium: write message
   alt subscribed to updates
       Message_API->Channel_Posting_API: subscribe to updates
       Channel_Posting_API->Message_API: <callback> update message status
   else polls for updates
       Message_API->Channel_Posting_API: <poll> get message status
   end
   Channel_Medium->Foreign_Node: receives message from channel
   @enduml


.. uml::

   @startuml
   hide empty description
   caption State of a message posted to a Channel Posting API

   [*] --> Received
   Received -right-> Confirmed
   Received --> Undeliverable
   Confirmed --> Revoked
   Revoked --> [*]
   Undeliverable --> [*]
   Confirmed -[dashed]-> [*]
   @enduml


States:

 - **Received**: The message either hasn't been written to the channel (perhaps the first attempt errored and will be attempted again) or has been written but awaiting confirmation.
 - **Confirmed**: The message has passed through the channel. Effectively the end state for most successful messages.

   + On a blockchain, this means that there are sufficient blocks on top.
   + On a DB this means that the message was commit to the table.

 - **Undeliverable**: The channel was unable to write the message and has stopped trying
 - **Revoked**: Confirmation was erroneously issued on a fork. We expect this to be extremely rare; it is a theoretical possibility.


A typical BlockchainChannel:

 - received message and writes to a DB, returning an ID
 - writes to the blockchain
 - waits (forever; stays in Received) and observes until:

   + multiple blocks are written on top of the chain (Confirmed)
   + OR observes that it was on a fork and the chain has moved from a previous block and the message was never written (Undeliverable)

It is the channel API's business to decide if it fails as Undeliverable on the first attempt, or whether it tries a few times (config value) before being marked as Undeliverable.


Channel Receiving API
---------------------

| ``POST /subscriptions`` - follows WEBSUB standard

.. uml::

   @startuml
   caption Receiving a message from a channel
   hide footbox
   
   box "Local Node" #LightGreen
       participant Message_Receiption_API
       participant Channel_Receiving_API
   end box
   participant Channel_Medium
   box "Foreign Node" #LightBlue
       participant Foreign_Node
   end box
   
   Message_Receiption_API->Channel_Receiving_API: subscribe to new messages
   Foreign_Node -> Channel_Medium: posts message to channel
   Channel_Receiving_API->Channel_Medium: get new message
   Channel_Receiving_API->Message_Receiption_API: <callback> post new message
   @enduml


| ``GET /messages/?sent_date=2020-01-12Z123456&receiver=AU`` - some method of querying for messages, optional?
|   or do we need to use a delivered_date? How do we handle the uncertainty of a block not being added to the chain after it's been sent?


A typical BlockchainChannel:
 
 - observes the blockchain and records new messages into a DB to keen track of what messages it has seen and what it hasn't
 - tells the subscription engine that a new message has arrived once a certain number of blocks are on top


**How does blockchain keep track of what it has and hasn't seen?**

Store a pointer that keeps track of the last block inspected. If head is above pointer (walk through next blocks until end?), then we are on the main branch. If not, walk backwards until you find the fork and mark any messages as false alarm.


.. uml::

   @startuml
   hide empty description
   caption State of a message being observed on a Channel Medium

   [*] --> Observed
   Observed -right-> Confirmed
   Observed --> False_Alarm
   Confirmed --> False_Alarm
   False_Alarm --> [*]
   Confirmed -[dashed]-> [*]
   @enduml


States:

 - **Observed**: The message has been seen on the channel medium, but we haven't confirmed that it is really there.
 - **Confirmed**: Means that the message is definitely on the channel medium. This is the point at which we publish the message.

   + On a blockchain, this means that there are sufficient blocks on top.
   + On a DB this means that the message was commit to the table. ie. the first time we observe the message it will also become confirmed.

 - **False_Alarm**: The message was seen on the channel medium but it has now disappeared.
   If the message had previously been **Confirmed**, the channel must publish an update about the message.
   If the message had only been **Observed** but not **Confirmed** we don't need to take any further action beyond changing the status of the message.

   + On a blockchain, this means we observed the message on a fork. We expect this to be extremely rare; it is a theoretical possibility.
   + On a DB, this shouldn't happen unless a message is deleted from the table.


Deploying a channel
-------------------

Process of setting up a channel:

 - spin up channel medium (optional)
 - spin up channel endpoint and configure with medium details, auth, ...
 - spin up second channel endpoint, same way
 - spin up new channel medium
 - spin up new endpoint pointing at new medium


**Example integration test node setup**

.. uml::

   @startuml
   caption Integration test network
   
   [Node A] as node_a
   [Node B] as node_b
   [Node C] as node_c

   [Channel A Endpoint 1] as channel_a_endpoint_1
   [Channel A Endpoint 2] as channel_a_endpoint_2
   [Channel A Endpoint 3] as channel_a_endpoint_3
   Database "Channel A DB" as channel_a_db

   [Channel B Endpoint 1] as channel_b_endpoint_1
   [Channel B Endpoint 2] as channel_b_endpoint_2
   Database "Channel B DB" as channel_b_db


   node_a -down-> channel_a_endpoint_1
   node_a -down-> channel_b_endpoint_1

   node_b -down-> channel_a_endpoint_2
   node_b -down-> channel_b_endpoint_2

   node_c -up-> channel_a_endpoint_3

   channel_a_endpoint_1 -down-> channel_a_db
   channel_a_endpoint_2 --> channel_a_db
   channel_a_endpoint_3 -up-> channel_a_db

   channel_b_endpoint_1 -down-> channel_b_db
   channel_b_endpoint_2 -down-> channel_b_db
   @enduml

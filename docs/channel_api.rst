Channel API
===========

A channel consists of three components:

 - one or more posting APIs,
 - one or more receiving APIs and,
 - a channel medium in the middle


.. uml::

   @startuml
   left to right direction
   title A channel with channel APIs and a channel medium
   
   cloud "Channel Medium" as cm
   
   package "Channel API - endpoint A" {
       [Channel Posting API] as a_cpa
       (post message) as a_pm
       [Channel Receiving API] as a_cra
       (receive message) as a_rm

       a_cpa --> a_pm
       a_pm --> cm
       a_cra <-- a_rm
       a_rm <-- cm
   }
   
   package "Channel API - endpoint B" {
       [Channel Posting API] as b_cpa
       (post message) as b_pm
       [Channel Receiving API] as b_cra
       (receive message) as b_rm

       b_cpa --> b_pm
       b_pm --> cm
       b_cra <-- b_rm
       b_rm <-- cm
   }

   package "Channel API - endpoint C (posting only)" {
       [Channel Posting API] as c_cpa
       (post message) as c_pm

       c_cpa --> c_pm
       c_pm --> cm
   }

   package "Channel API - endpoint D (receiving only)" {
       [Channel Receiving API] as c_cra
       (receive message) as c_rm

       c_cra <-- c_rm
       c_rm <-- cm
   }
   @enduml


Notes:

 - Posting to a channel is a broadcast mechanism; receivers need to determine if a message is meant for them or not
 - Sender authorisation is implemented by the channel
 - Sender verification is the responsibility of the receiver
 - Non-repudiation may be guaranteed by the channel medium


.. uml::

   @startuml
   title A channel within the context of an Intergov node

   package "Channel" {
       [Channel Posting API] --> [Channel Medium]
       [Channel Posting API] --> [<<db>>\nOutgoing messages]
       [Channel Receiving API] <-- [Channel Medium]
       [Channel Receiving API] --> [<<db>>\nIncoming messages]
   }

   package "Messages API" {
       [Message Router] --> [Channel Posting API]
       [Channel Posting API] --> [Message Router] : callback when message state changes (replaces blockchain observer)
       [Channel Receiving API] --> [Message Reception API] : callback when a message is received
   }
   @enduml


**Channel Posting API**

| ``POST /messages``
| ``GET /messages/<id>``
| ``GET /messages/<id>/status``

.. uml::

   @startuml
   title Posting a message to a channel
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
   title State of a message posted to a Channel Posting API

   [*] --> Received
   Received --> Confirmed
   Confirmed : Means that the message has passed through the channel.\nOn a blockchain, this means that there are sufficient blocks on top.\nOn a DB this means that the message was commit to the table.\nEffectively the end state for most successful messages.
   Received --> Undeliverable
   Undeliverable : The channel was unable to write the message\nand has stopped trying to confirm
   Confirmed --> Revoked
   Revoked : Confirmation was erroneously issued on a fork.\nWe expect this to be extremely rare; \nit is a theoretical possibility.
   Revoked --> [*]
   Undeliverable --> [*]
   Confirmed -[dashed]-> [*]
   @enduml


A typical BlockchainChannel:

 - received message and writes to a DB, returning an ID
 - writes to the blockchain
 - waits (forever; stays in Received) and observes until:

   + multiple blocks are written on top of the chain (Confirmed)
   + OR observes that it was on a fork and the chain has moved from a previous block and the message was never written (Undeliverable)

It is the channel API's business to decide if it fails as Undeliverable on the first attempt, or whether it tries a few times (config value) before being marked as Undeliverable.


Process of setting up a channel:

 - spin up channel medium (optional)
 - spin up channel endpoint and configure with medium details, auth, ...
 - spin up second channel endpoint, same way
 - spin up new channel medium
 - spin up new endpoint pointing at new medium


**Channel Receiving API**

| ``POST /subscribe`` - WEBSUB standard

.. uml::

   @startuml
   title Receiving a message from a channel
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


| ``GET/POST /<subscription endpoints>`` - WEBSUB standard
| ``GET /messages/?sent_date=2020-01-12Z123456&receiver=AU`` - or do we need to use a delivered_date? How do we handle the uncertainty of a block not being added to the chain after it's been sent?

A typical BlockchainChannel:
 
 - observes the blockchain and records new messages into a DB to keen track of what messages it has seen and what it hasn't
 - tells the subscription engine that a new message has arrived


Blockchain: pointer keeps track of last block inspected. If head is above pointer, then we are on the main branch. If not, walk backwards until you find the fork and mark any messages as false alarm.


.. uml::

   @startuml
   title State of a message being observed on a Channel Medium

   [*] --> Observed
   Observed --> Confirmed : Publish
   Confirmed : Means that the message is definitely on the channel medium.\nOn a blockchain, this means that there are sufficient blocks on top.\nOn a DB this means that the message was commit to the table.\nThis is the point at which we publish the message.
   Observed --> False_Alarm : No action needed; the message was never published
   Confirmed --> False_Alarm : Publish update about the message
   False_Alarm : Confirmation was erroneously issued on a fork.\nWe expect this to be extremely rare; \nit is a theoretical possibility.
   False_Alarm --> [*]
   Confirmed -[dashed]-> [*]
   @enduml

blockchain

   Received --> Undeliverable
   Undeliverable : The channel was unable to write the message\nand has stopped trying to confirm
   Confirmed --> Revoked
   Revoked : Confirmation was erroneously issued on a fork.\nWe expect this to be extremely rare; \nit is a theoretical possibility.
   Revoked --> [*]
   Undeliverable --> [*]


**Channel Auth**

Purpose: to allow only authorised nodes to post to it.

Channel operator's business to determine access requirements for the channel.

For example, if a node operator is operating private channel APIs for its own use, and not allowing any other nodes to use their channel APIs, then network level security may be sufficient. Similarly, a developer may use docker networking connections to restrict access without implementing any explicit access controls. However, if a channel operator wanted to support multiple nodes, then they would need to develop a satisfactory access control regime, sufficient for the requirements of that channel.

A channel may have a bunch of nodes using it, but tens not 1000s. So manual/devops style auth configuration is fine.

Pilot 2 implementation: Given all nodes will also be channel operators, either subnet only networking or whitelisting IP addresses/API Gateway SIG4 certs etc...


**Node Auth**

Purpose: to make sure the party sending the message is allowed to send that kind of message to that destination.

V short term (MVP), we give third parties an intermediate API (chambers APP) which is allowed to send a message.

Better (MVP 2), we use OIDC and trust the identity provider (IDP) to make authorisation claims (eg. IS A chamber of commerce) and then apply policies ourselves (eg. MUST BE a chamber of commerce)

Example:

 - Cognito user pool = AD with roles
 - Node operator maintains the AD

Long term, we'd use TDIF compliant IDP and some mechanism? for associating accreditation with business identities. Eg. DFAT might maintain a list of authorised chamber ABNs and then a company might authenticate using an ATOIDP as that ABN.


Node validation and verification:

 - validate that the message/document is a valid format
 - verify that the message/document is verified (authoritative claims (airport says airport related business facts) vs verified claims (airport says someone told us this, and we checked it))



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

TODO: Need examples of documents that might be passed from end to end

.. uml::

Node is a message router. Technical ACK - I got the message and I downloaded the documents.

::

    Sender: AU
    Receiver: CN
    Subject: ID of object
    Object: the document
    Predicate: states of the object


.. uml::

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

| ``POST /messages/``
|   returns ``<id>`` aka ``sender_ref``
| ``GET /messages/<id>``
| ``GET /messages/<id>/status``
| ``GET /messages/<id>/journal``
|   returns a list of all state changes for this message


.. uml::

   @startuml
   title Posting to channel state

   [*] --> Pending
   Pending : either posted to the channel or waiting\n  to be bundled with other messages
   Pending --> Sent : Sent to the channel\nas a single message
   Pending --> Bundled
   Pending --> Failed : If the message cannot be\nsent (pre-channel fail)
   Bundled --> Sent
   Bundled : A "bundler" (perhaps the router) groups messages,\n  puts them into a document and\n  sends a message with that document as the object.
   Bundled : If the bundled message fails, we think the messages\n  should be set back to pending\n  and can be bundled as appropriate at the time.
   Sent --> Delivered
   Sent : We have successfully asked the channel to\n  deliver the message. Delivery is async.
   Sent --> Pending : If the message was not\nsuccessfully delivered,\nit must be tried again
   Sent --> Failed : If the message cannot be delivered\nafter trying again (channel fail)
   Delivered : The channel reports that\n  delivery has been successful.
   Delivered -[dashed]-> [*] : Semi-terminal\nSuccess is a zombie,\nonly failure is permanent
   Delivered -up-> Withdrawn
   Withdrawn : The message was thought to be delivered\n  but that was in error.\nUnlikely, but necessary due to\n  the vagaries of blockchain.
   Withdrawn --> Pending
   Failed --> [*]
   @enduml


``/messages/<id>/acknowledgement``

.. uml::

   @startuml
   title Acknowledgement state

   [*] --> Unacknowledged
   Unacknowledged --> TechnicalAck
   Unacknowledged --> TechnicalNack
   TechnicalAck --> [*]
   TechnicalNack --> [*]
   @enduml


Notes:

Bundled messages would be put into a "message list" document and the "bundle message" is a message about a document that is a list of messages, not a message about a single document.

Blockchain problems that we are trying to deal with:

 - If the message is put on the chain but we don't consider it delivered and China download the document and ack it anyway, it may end up being on a fork and not ever sent.


**Message reception state:**

TODO: TBD


Channel Technical Details
-------------------------






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



**Example of end to end scenario**

Certificate of Origin:

 - Preferential - issued under the terms of an FTA
 - Non-preferential - assertion of origin only
 - Issued by an authoritative body (usually a chamber of commerce in Australia) which is accredited by a government body (AusTrade?)
 - Issued for each consignment
 - Can be updated (eg. if the flight details change)


Currently:

A Certificate of Origin is created by a chamber (eg. AKI) at the request of an exporter (eg. Wine Exporters Inc.). It is a paper document with a wet seal. The chamber gives it to the exporter or the freight forwarder (eg. DHL). The exporter gives it to the importer (Wine Importer and Distributor of China Inc.) who gives it to their Customs Agent. Customs Agent deals with the customs authority who look at the document and the consignment and confirm that it is what it says it is.

Sometimes the customs official does not believe that the CoO is genuine and they will ask China Customs to confirm, who asks Australia Customs, who asks the Chamber, who says yes, and it goes back down the chain to the customs agent. In that time, the consignment may have gone off.


The new way:

 - Exporter asks for CoO from chamber.
 - Chamber uses Business Service Layer (Origin document producer API) to generate a digital CoO which returns a hash/QR Code that represents the notarised CoO.
 - This QR Code goes to the Exporter and Freight Forwarder.
 - The Origin Document Producer (what name did Steve use?) builds the digital document, gets it notarised (TradeTrust) and sends it to a Domestic Node (document and message).
 - The Domestic Node stores the document and routes the message to receiver using a channel
 - The Foreign Node is notified of the message and retrieves the document from the Domestic Node. Some Technical ACK occurs to confirm that the document has been successfully retrieved.
 - The Foreign Node notifies any foreign systems that subscribed about the new message/document. Eg. Chinese Customs IT system




**Integration test node setup**

.. uml::

   @startuml
   title Integration test network
   
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

   node_a -> channel_a_endpoint_1
   node_a -> channel_b_endpoint_1

   node_b -> channel_a_endpoint_2
   node_b -> channel_b_endpoint_2

   node_c -> channel_a_endpoint_3

   channel_a_endpoint_1 -> channel_a_db
   channel_a_endpoint_2 -> channel_a_db
   channel_a_endpoint_3 -> channel_a_db

   channel_b_endpoint_1 -> channel_b_db
   channel_b_endpoint_2 -> channel_b_db

   @enduml




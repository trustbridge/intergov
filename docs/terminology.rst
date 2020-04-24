Terminology
===========

TODO: define and describe these things



======================= ============================================================================================================
Term                    Description
======================= ============================================================================================================
Channel                 Implementation of an agreement between jurisdictions to exchange particular types of messages.
Channel Policy          Rules, expressed in a common business language, that describe the acceptable use of the channel.
Channel Media           Append-only database where channel messages are written. Presumably a distributed database, e.g. blockchain.
Channel Endpoint        Deployed system that can read and write to the channel media.
Channel API             Abstraction over channel media. Feature of the Channel Endpoint used by the IGL Node to send messages.
Channel Keys            Notional mechanism for restricting access (in particular write access) to legitimate channel endpoints.
======================= ============================================================================================================



Jurisdiction
------------


Node User
---------


Messages
--------


Documents
---------


Claim
-----


Node
----

Nodes act on behalf of jurisdictions and are authorised to do so by the jurisdiction.
Messages are addressed to jurisdictions, not nodes.
Node users use the node to send a message to another jurisdiction, not nodes or channels.


Channel
-------

Notes:

 - Posting a message to a channel is a broadcast mechanism; receivers need to determine if a message is meant for them or not
If there are multiple nodes acting on behalf of a jurisdiction and subscribed to a particular channel, all of those nodes will receive all messages addressed to that jurisdiction that are posted to that channel.

 - Sender authorisation is implemented by the channel
 - Sender verification is the responsibility of the receiver

 - Non-repudiation may be guaranteed by the channel medium

Question: Is posting to a channel always broadcast? Or may some channel mediums deliver only to the intended recipient?
And are the above statements all true?


Channel Endpoint
----------------


Channel Medium
--------------

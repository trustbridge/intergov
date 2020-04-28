Terminology
===========


Glossary
--------

+-------------------+-------------------------------------------------------+
| Term              | Description                                           |
+===================+=======================================================+
| Channel           | Implementation of an agreement between jurisdictions  |
|                   | to exchange particular types of messages.             |
+-------------------+-------------------------------------------------------+
| Channel Policy    | Rules, expressed in a common business language, that  |
|                   | describe the acceptable use of the channel.           |
+-------------------+-------------------------------------------------------+
| Channel Media     | Append-only database where channel messages are       |
|                   | written. Presumably a distributed database,           |
|                   | e.g. blockchain.                                      |
+-------------------+-------------------------------------------------------+
| Channel Endpoint  | Deployed system that can read and write to the        |
|                   | channel media.                                        |
+-------------------+-------------------------------------------------------+
| Channel API       | Abstraction over channel media.                       |
|                   | Feature of the Channel Endpoint                       |
|                   | used by the IGL Node to send messages.                |
+-------------------+-------------------------------------------------------+
| Channel Keys      | Notional mechanism for restricting access             |
|                   | (in particular write access)                          |
|                   | to legitimate channel endpoints.                      |
+-------------------+-------------------------------------------------------+
| Channel Operator  | Party with access to the Channel Keys,                |
|                   | who provides the Channel Endpoint.                    |
+-------------------+-------------------------------------------------------+
| Channel Manager   | Party responsible for the channel.                    |
|                   | May have the ability to grant/revoke Channel Keys.    |
+-------------------+-------------------------------------------------------+
| Channel           | Mechanism to restrict access to the Channel API,      |
| Authentication    | So authorised Nodes can access the Channel Endpoint.  |
|                   | Not to be confused with Node Authentication           |
|                   | (restricting access to the Node to Node Users),       |
|                   | Channel Keys (used to restrict access to Channel      |
|                   | Media, to Channel Operators)                          |
|                   | or document issuer / verification mechanisms.         |
+-------------------+-------------------------------------------------------+



Notes
-----

.. uml::

   package "National Infrastructure" {
      component node as "Node"
      interface channel_api as "Channel\nAPI"
      note left of channel_api : Channel Authentication required\nto access the Channel API
      component channel_endpoint as "Channel\nEndpoint"
      actor channel_operator as "Channel\nOperator"
      actor node_operator as "Node\nOperator"
      actor channel_manager as "Channel\nManager"
      note "Between the Channel Media\nand the Channel Endpoint,\nthe Channel Policy is enforced" as note_chan_policy
   }
   cloud {
      database channel_media as "Channel\nMedia"
      note "Channel Manager configures the Channel Media.\nChannel Operator uses Channel Keys to\naccess (write to) the Channel Media." as note_chan_keys
      note "Channel Media is distributed infrastructure\nsupporting the Channel Policy." as note_chan_media
   }

   node -down-> channel_api
   channel_api -down- channel_endpoint
   channel_endpoint -down-> channel_media
   channel_operator -left-> channel_endpoint
   node_operator -left-> node
   channel_manager -left-> channel_operator
   note_chan_keys .left. channel_media
   channel_operator .down. note_chan_keys
   channel_manager .down. note_chan_keys
   channel_endpoint .left. note_chan_policy
   note_chan_media .right. channel_media


Jurisdiction
^^^^^^^^^^^^


Node User
^^^^^^^^^


Messages
^^^^^^^^


Documents
^^^^^^^^^


Claim
^^^^^


Node
^^^^

Nodes act on behalf of jurisdictions and are authorised to do so by the jurisdiction.
Messages are addressed to jurisdictions, not nodes.
Node users use the node to send a message to another jurisdiction, not nodes or channels.


Channel
^^^^^^^

Notes:

 - Posting a message to a channel is a broadcast mechanism; receivers need to determine if a message is meant for them or not
If there are multiple nodes acting on behalf of a jurisdiction and subscribed to a particular channel, all of those nodes will receive all messages addressed to that jurisdiction that are posted to that channel.

 - Sender authorisation is implemented by the channel
 - Sender verification is the responsibility of the receiver

 - Non-repudiation may be guaranteed by the channel medium

Question: Is posting to a channel always broadcast? Or may some channel mediums deliver only to the intended recipient?
And are the above statements all true?


Channel Endpoint
^^^^^^^^^^^^^^^^


Channel Medium
^^^^^^^^^^^^^^

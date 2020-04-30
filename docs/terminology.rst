Terminology
===========


Glossary
--------

+-------------------+-------------------------------------------------------+
| Term              | Description                                           |
+===================+=======================================================+
| Node Users        | Business Layer Systems that communicate with one or   |
|                   | more Nodes to send and receive messages to other      |
|                   | Jurisdictions.                                        |
+-------------------+-------------------------------------------------------+
| Node API          | A set of APIs used to send and receive messages over  |
|                   | channels.                                             |
+-------------------+-------------------------------------------------------+
| Node              | Service that provides the Node API, sends messages    |
|                   | (after validating them) to a channel on behalf of a   |
|                   | jurisdiction, and recieves then disburses messages    |
|                   | sent to the jurisdiction over the channels.           |
|                   |                                                       |
|                   | The Node is authorised (Node Accreditation) to send   |
|                   | and recieve messages messages on behalf of the        |
|                   | Jurisdiction. The node validates each messages to     |
|                   | to ensure compliance with the channel policy (from    |
|                   | the juridictional context). In other words, nodes are |
|                   | trusted by the accrediting body to apply local        |
|                   | knowledge to the interpretation of channel policy in  |
|                   | that jurisdiction.                                    |
|                   |                                                       |
|                   | The Node is also a router. It decides which channel   |
|                   | (Node Routing Policy) each valid message should be    |
|                   | used to sent the message to the recipient             |
|                   | Jurisdiction.                                         |
|                   |                                                       |
|                   | Nodes also receive inbound messages, retrieves the    |
|                   | associated document (object) and store these for Node |
|                   | Users, as well as notifying the appropriate Node      |
|                   | when new messages have been received.                 |
|                   |                                                       |
|                   | - Nodes act on behalf of jurisdictions and are        |
|                   |   authorised to do so by the jurisdiction (Node       |
|                   |   Accreditation).                                     |
|                   | - Messages are addressed to jurisdictions, not nodes. |
|                   | - Node Users use the node to send a message to        |
|                   |   another jurisdiction, not nodes or channels.        |
|                   | - Node Operators may use trustbridge/intergov         |
|                   |   software (reference implementation) or they may     |
|                   |   create their own systems that comply with the open  |
|                   |   standards.                                          |
|                   |                                                       |
+-------------------+-------------------------------------------------------+
| Channel           | Implementation of an agreement between jurisdictions  |
|                   | to exchange particular types of messages.             |
|                   |                                                       |
|                   | - Node Users should understand that all nodes on a    |
|                   |   channel can potentially see all messages posted to  |
|                   |   If there are multiple nodes acting on behalf of a   |
|                   |   jurisdiction, and subscribed to a particular        |
|                   |   channel, all of those nodes will receive all        |
|                   |   messages addressed to that jurisdiction that are    |
|                   |   posted to that channel.                             |
|                   | - The "side-tree" protocol bundles multiple messages  |
|                   |   in a single message on the wire. It is up to the    |
|                   |   Node to unpackage these bundles. Other nodes, who   |
|                   |   are not the recipient (Nodes from other             |
|                   |   Jurisdictions) will NOT be able to access and       |
|                   |   unbundle these messages.                            |
|                   | - The channel implementation MAY validate some        |
|                   |   aspects of the message, but the Node MUST send only |
|                   |   valid messages to the channel. For example, a       |
|                   |   Channel Endpoint may reject messages with invalid   |
|                   |   sender or recipient juridisctions, or invalid       |
|                   |   message predicates.                                 |
|                   |                                                       |
+-------------------+-------------------------------------------------------+
| Channel Policy    | Rules, expressed in a common business language, that  |
|                   | describe the acceptable use of the channel.           |
+-------------------+-------------------------------------------------------+
| Channel Media     | Append-only database where channel messages are       |
|                   | written. Presumably a distributed database.           |
|                   |                                                       |
|                   | - Channel media are pan-jurisdictional (not owned or  |
|                   |   controlled by any one jurisdictions) and shared by  |
|                   |   all the nodes.                                      |
|                   | - Candidate technologies for Channel Media include    |
|                   |   public blockchaim and private blockchain (when each |
|                   |   Jurisdiction has appropriate access for Channel     |
|                   |   Management and Operations.                          |
|                   | - Channel media MAY convey cryptographic protocol     |
|                   |   characteristics to the channel e.g. non-repudiation |
|                   | - Channel media technology is generally unspecified,  |
|                   |   to ensure Jurisdictions are free to negotiate the   |
|                   |   most appropriate technology for a given channel.    |
|                   |                                                       |
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

      actor "Node\nUser" as node_user
      interface channel_api as "Channel\nAPI"
      interface node_api as "Node\nAPI"
      component "Identiy\nProvider" as idp
      
      note "Channel Authentication required\nto access the Channel API.\nIf the Node Operator\nis also the Channel Operator,\nthen channel authentication may be\nimplemented at the network layer." as note_chan_auth
      note_chan_auth .down. channel_api
      
      package "Operations" {
         component node as "Node"
	 component channel_endpoint as "Channel\nEndpoint"
	 actor channel_operator as "Channel\nOperator"
         actor node_operator as "Node\nOperator"
	 note "The Node Operator may or may not be\nthe same party as the Channel Operator.\nThe Channel Endpoint may be private\nto the Node, or it may be independant of\nthe Node (potentially shared between\nnodes)." as note_nod_chan_op
	 note_nod_chan_op .right. channel_operator
	 note_nod_chan_op .left. node_operator
	 note_nod_chan_op .up. node
	 note_nod_chan_op .up. channel_endpoint
      }
      package "Governance" {
         actor node_accred as "Node\nAccreditation"
         actor channel_manager as "Channel\nManager"
	 note "The machinery of government\nmay comprise different agencies\nthat negotiate channels independantly\nbut node accreditation should probably\nbe administered centrally." as note_mog
	 node_accred .right. note_mog
	 note_mog .right. channel_manager
	 
      }
      note "Between the Channel Media\nand the Channel Endpoint,\nthe Channel Policy is enforced" as note_chan_policy
   }
   cloud "Extra-Jurisdictional" {
      database channel_media as "Channel\nMedia"
      note "Channel Manager configures the Channel Media.\nChannel Operator may use Channel Keys so that\nthe Channel Endpoint can access (write to) the\nChannel Media." as note_chan_keys
      note "Channel Media is the pan-jurisdictional\nprotocol implementation, negotiated\nthe (two or more) jurisdictions. While\nChannel Policy is bound to the semantics\nof local regulation, the Channel Media is\nbound to standardised international semantics." as note_chan_media
   }

   node_accred -up-> node_operator
   node -up-> channel_api
   node_api -down- node
   channel_api -down- channel_endpoint
   channel_endpoint -down-> channel_media
   channel_operator -up-> channel_endpoint
   node_operator -up-> node
   channel_manager -up-> channel_operator
   note_chan_keys .left. channel_media
   channel_endpoint .down. note_chan_keys
   channel_manager .down. note_chan_keys
   channel_endpoint .up. note_chan_policy
   note_chan_media .up. channel_media

   node -up-> idp
   node_user -down-> idp
   node_user -down-> node_api

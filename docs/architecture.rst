Architecture
------------

High level overview:

.. graphviz:: architecture_component_diagram_overview.dot


Document API and components:

.. graphviz:: architecture_component_diagram__documents_api.dot


Message API and components:

.. graphviz:: architecture_component_diagram__messages_api.dot


Channel API and components:

.. graphviz:: architecture_component_diagram__channel.dot

With processes:

.. graphviz:: architecture_component_diagram__channel__with_uc.dot


| Document API - storage of local documents and retrieval of foreign documents
| Message API - posting messages to a foreign jurisdiction and retrieving messages from a foreign jurisdiction
| Subscription API - a hub to subscribe to updates about messages

Purpose
=======

The TrustBridge InterGov codebase is
a Proof Of Concept (POC) implementation
of the edi3 Inter Government Ledger (IGL) Specification.

The specific goal of this codebase
is to create infrastructure for
an independant IGL "Node".

This node is as it would be operated by a Country.
It provides the interfaces required by the regulated community,
(i.e. B2G interfaces)
and it interfaces with "Channels"
which are are used for communicating with other jurisdictions
(i.e. G2G interfaces).
It provides a suite of microservices
that reliably route and deliver messages between the two.


Prototype edi3 standards
------------------------

See https://edi3.org/icl/
for details of the interfaces
that are implemented here.

This software is organised using a microservice architecture.
The file **DEPLOYMENT.rst** contains instructions
for running these components together in a local workstation.

There are three basic types of deployable component:

* Microservices, that provide REST web services
  and depend on statefull backing services.
* Backing Services, which are responsible for shared state
  between API Microservices and Worker Processes.
* Worker Processes, which perform asynchronous tasks.

A very high level description of the design looks like this;
Each jurisdiction operates a suite of services,
that provides the following types of integration surface:

* Government to Government (G2G) "channels",
  These may use distributed ledger technology,
  but the details are hidden behind a "Channel API".
* Regulated Community APIs.
  These are used by members of the regulated community
  to interact with their Government (B2G/G2B).
  These interactions are are either direct with the API
  or indirect, through some commuity systems and identity provider.
* The Document API. This is accessed by the regulated community,
  but also (as policy allows) by the counterparty
  of associated messages on the G2G channels.
  This also implies the use of an identity provider.


Support the UN process
----------------------

The business case and background of the edi3 work is published at https://uncefact.unece.org/display/uncefactpublic/Cross+border+Inter-ledger+exchange+for+Preferential+CoO+using+Blockchain


Open Source Reference Implementation
------------------------------------

The purpose of the POC
is to use a real working system
to evaluate the edi3 specification design decisions.
We believe this will lead to a superior design
than just developing the specifications on a theoretical basis,
before trying to apply them.

This implementation is tracking the specifications
on the edi3 web site.
As the specifications change,
we intend to modify this software to keep up.
This software will remain a POC status
as long as the specifications are considered a working draft,
however, the software microservice architecture
should support future large scale deployment
and long term maintainability.

The status of the software will be updated to BETA
when it is considered appropriate for pilot implementation.
In the meantime, contributions are welcome
at https://github.com/trustbridge

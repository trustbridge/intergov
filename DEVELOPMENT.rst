Development
===========

Development occurs in GitHub at https://github.com/trustbidge/intergov

Please note:
 * The code is GPL v3 (see /LICENCE for details).
 * Pull requests welcome!
 * Contributions remain the intellectual property of the contributors, per Collective Code Construction Contract as described at https://rfc.zeromq.org/spec:22/C4/
 * Please do open tickets for discussion, help requests, etc.
 * We have adopted the code of conduct published at https://www.contributor-covenant.org/

TODO: create readthedocs site and point to it.


Quickstart
----------

Intergov is tighly coupled with the countries, so if you want to start it locally
you will do it for some test countries. We have provided 2 demo setups - for Australia
and China; it could be any other - just copy the docker-compose and env files and change variables accordingly.

To start Australian setup:

   * touch demo-au-local.env
   * PORTPREFIX=50 COMPOSE_PROJECT_NAME=au docker-compose -f demo.yml up

For China:

   * touch demo-cn-local.env
   * PORTPREFIX=60 COMPOSE_PROJECT_NAME=cn docker-compose -f demo.yml up

About env files: the setups share demo-default.env and have demo-{country_name}.env importer (commited, contains country-specific values) and demo-{country_name}-local.env (gitignored).

Local files could probably contain at least ``IGL_MCHR_SHARED_CHANNEL_URL`` variable - which is either some remote or local endpoint available to the containers (useful channel example - https://github.com/trustbridge/shared-db-channel)

Setups are linked through the ``intercountries`` network and have hostnames equal to their container names (AU_ig_document_api and CN_ig_document_api). obj_spider has this network and can access document APIs from the both setups for example.

Or use the pie.py helper:

   (this needs to be rewritten as well as the script itself)

   touch demo-local.env
   python3.6 pie.py intergov.build
   python3.6 pie.py intergov.start
   python3.6 pie.py intergov.tests.unit
   python3.6 pie.py intergov.tests.integration

For integration tests to succeed you need to have all containers started and running (run ``up`` without parameters)

Expect the last part (integration tests) to take a minute or two.

You can generate docs too with:

   python3.6 pie.py docs.create_docker_image
   python3.6 pie.py docs.build_docs
   # alternative: starts a server that hosts and autobuilds the docs on changes - http://localhost:8998/
   python3.6 pie.py docs.build_docs_autobuild


Project structure
-----------------

* intergov - the source code
* intergov/repos - all repos (entities to store data)
* intergov/repos/base - base repos, dealing with real carrier (S3, minio, elasticmq, sqs, etc)
* intergov/apis - set of Flask applications which offer REST API endpoints
* intergov/processors - set of Python scripts which work constantly in the background and do things
* tests - the tests for ``intergov`` folder


The code
--------

* is structured following a "hexagonal architecture pattern".
* in intergov/repos/ is dirty with external dependancies and IO.
* in intergov/domain is a "functionally pure" OO model (no side effects).

The APIs provides by the code in intergov/repos/ are strict,
they only accept and produce domain model instances.
This means it should be possible to make alternate repo implementations
using different underpinning technologies
without having to change these interfaces.

The code in use_cases/ is worth noting.
It implements business logic using pure domain objects,
interacting with repo objects as necessary
to manage IO and dependancies
(indirectly, through the API of the repo objects)

Note the pattern:

* use_case Classes are instantiated with repo instances as parameters
* use_case Objects have executor methods (that may or may not take parameters)
* the use_case itself is pure, like the domain model,
  except for it's interactions with repo objects.

This means that we can thoroughly test the business logic
using mock repo objects.
You can see that happening in tests/

Finally, most of the other subdirectories in intergov/
are executable components.
These are typically either headless workers
(processes) or REST APIs.
These components are generally stateless
(in the "12 factor" sense,
configured by environment variables etc.)
and interact with each other through APIs
or backing services (databases, queues, etc).
They are designed to be deployed in HA configurations
behind load ballancers (with dynamic scaling, etc).

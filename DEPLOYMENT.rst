Deployment
==========

This document explains how to start the thing and configuring it.

First, do this so you have the submodules:

.. code-block::
   bash

   git submodule update --init --recursive


Docker approach
---------------

We have a docker configured to:

* read it's configuration from ``*.env`` files in this directory
* run the service
* provide elasticmq, postgres and minio servers
* save data to ./var/ directory to persist it between runs

Once run it starts all requirements and tries to run tests (``base`` container
which exists just after it - it's fine). Also other containers are started and expected
to keep working. Press control-C to stop it and use ``down`` instead of ``up`` to
remove the containers, add ``--build`` flag when you have changed the code and docker
didn't see it (or just to be safe after code is updated).

.. code-block::
    bash

    docker-compose up

Minio (S3 analogue) has nice UI (http://localhost:9000/) - secrets are in docker-compose.yml file.

Unittests will be run on each startup, you may disable it by commenting `tests` service in the
docker-compose file.

If you want to run integration tests:

.. code-block::

    docker-compose run tests-unit sh -c "cd /src && make test-integration"
    # or
    docker-compose run tests-unit sh -c "cd /src && py.test tests/integration"


If you want to run another installation (like second country) use demo-dc-cn.yml file
and create ``demo-local-cn.env`` file (git excluded, feel free to add your settings):

    IGL_COUNTRY=CN
    IGL_DEFAULT_S3_HOST=cnminio.cnint
    IGL_DEFAULT_SQS_HOST=cnelasticmq
    IGL_DEFAULT_POSTGRES_HOST=cnpostgresql
    IGL_PROC_BCH_MESSAGE_RX_API_URL=http://cnmessage_rx_api:5100/messages
    IGL_PROC_BCH_MESSAGE_API_ENDPOINT=http://cnmessage_api:5101/message/{sender}:{sender_ref}

It's not automated because it's easy to start yourself and not needed by everyone yet.

Configuration
-------------

Is done using env variables.
Boolean values must be strings and either true or false. JSON values must be rendered objects as a string. Everything else is a string. Lack of value uses default one, which is item-specific, or None if no default is provided.

* IGL_COUNTRY_DOCUMENT_REPORTS - string with JSON dict, keys are 2 character countries names, values are repo urs (http://.../..)
* IGL_DEBUG - enable/disable DEBUG for Flask instances
* IGL_TESTIG - enable/disable TESTING for Flask instances.

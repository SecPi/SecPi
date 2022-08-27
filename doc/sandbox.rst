#########################
SecPi development sandbox
#########################


*************
Prerequisites
*************

Choose AMQP broker.

- GarageMQ: A lightweight AMQP broker written in Golang.
  https://github.com/valinurovam/garagemq

- RabbitMQ: The reference AMQP broker written in Erlang.
  https://github.com/rabbitmq/rabbitmq-server

Start an AMQP broker using Docker::

    # GarageMQ
    docker run --rm -it --publish=5672:5672 amplitudo/garagemq

    # RabbitMQ
    docker run --rm -it --publish=5672:5672 rabbitmq:3.9


*****
Setup
*****

Acquire sources::

    git clone https://github.com/isarengineering/SecPi
    cd SecPi

Setup Python virtualenv and install dependencies::

    python3 -m venv .venv
    source .venv/bin/activate
    pip install --editable=.[test,develop]


*******
Operate
*******

Start all services::

    # Activate virtualenv.
    source .venv/bin/activate

    # Run software tests.
    pytest

    # Start Manager, Worker, and Webinterface, in different terminals.
    ./startup.sh manager
    secpi-worker --app-config worker/config.json
    ./startup.sh webinterface


*******
Vagrant
*******

=====
About
=====

The repository ships a ``Vagrantfile`` which should get you started easily. Within the
virtual machine, two directories will be provisioned:

- ``/usr/src/secpi``
  This directory mounts the repository root folder on the host machine,
  that is, the current directory.

- ``/opt/secpi``
  This directory holds the virtual environment for the SecPi installation on Linux.

On top of that, the program ``secpi-worker`` is available in the global program search
path.


=====
Usage
=====

::

    # Provision and start virtual machine and log in.
    vagrant up
    vagrant ssh

    # Run SecPi Worker.
    secpi-worker --app-config /usr/src/secpi/worker/config.json

Run software tests::

    vagrant ssh
    source /opt/secpi/bin/activate
    cd /usr/src/secpi
    pytest


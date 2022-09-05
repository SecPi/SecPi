##############
SecPi handbook
##############


**********
By example
**********


Common
======

Submit operational shutdown message::

    # Manager.
    echo '{"action": "shutdown"}' | amqp-publish --routing-key=secpi-op-m

    # Worker #1.
    echo '{"action": "shutdown"}' | amqp-publish --routing-key=secpi-op-1

    # Webinterface
    echo '{"action": "shutdown"}' | http POST http://localhost:8000/operational


Manager
=======

The Manager receives and mediates, amongst others, setup activation messages and alarm messages.
Setup activation messages are received from SecPi Web, and forwarded to the Workers.
Alarm messages are received from the Workers, and dispatched to the Notifiers.

Activate setup::

    # Watch bus.
    amqp-consume --queue=secpi-on_off cat

    # Emulate "activate setup" bus message.
    echo '{"setup_name": "testdrive", "active_state": true}' | amqp-publish --routing-key=secpi-on_off

Raise alarm per message to the AMQP bus::

    # Watch bus.
    amqp-consume --queue=secpi-alarm cat

    # Emulate "raise alarm" bus message.
    echo '{"worker_id": 1, "sensor_id": 1, "message": "Got TCP connection, raising alarm", "datetime": "2022-08-27 02:33:33"}' | amqp-publish --routing-key=secpi-alarm



Worker
======

Workers are observing sensors and publish corresponding alarm trigger messages
to the bus. An example for easily triggering the ``network.TCPPortListener``
sensor on port 1234 is::

    echo hello | socat - tcp:localhost:1234



Webinterface
============

Activate setup::

    echo '{"id": 1}' | http POST http://localhost:8000/activate

Deactivate setup::

    echo '{"id": 1}' | http POST http://localhost:8000/deactivate

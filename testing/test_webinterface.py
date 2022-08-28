import logging

import requests

from testing.util.service import WebinterfaceServiceWrapper

logger = logging.getLogger(__name__)


def test_webinterface_start_stop():
    """
    Start Webinterface and immediately shut it down again. Verify that the log output matches the expectations.
    """

    # Start service in separate process.
    service = WebinterfaceServiceWrapper()
    service.run()

    # Send service a shutdown signal.
    service.shutdown()

    # Read application log.
    application_log = service.read_log()

    # Verify everything is in place.
    assert "Configuring Webinterface" in application_log
    assert "Using template path" in application_log
    assert "Loading configuration from testing/etc/config-web.json" in application_log
    assert "Connecting to database sqlite:///secpi-database-testing.sqlite" in application_log
    assert "Initializing Webserver" in application_log
    assert "Connecting to AMQP broker at localhost:5672" in application_log
    assert "Connecting to AMQP broker successful" in application_log
    assert "AMQP: Connected to broker" in application_log

    # TODO: Occasionally missing?
    assert "Serving on http://0.0.0.0:8000" in application_log
    assert "ENGINE Bus STARTED" in application_log

    assert "Got message on operational endpoint: {'action': 'shutdown'}" in application_log
    assert "Shutting down" in application_log
    assert "Stop consuming AMQP queue" in application_log
    assert "Disconnected from RabbitMQ at localhost:5672" in application_log
    assert "ENGINE Bus STOPPING" in application_log
    assert "ENGINE Bus EXITED" in application_log


def test_webinterface_with_activate(webinterface_service):
    """
    Start Webinterface, create, activate, and deactivate setup. Verify that the log output matches the expectations.
    """

    # Create a setup.
    requests.post(url="http://localhost:8000/setups/add", json={"name": "secpi-testing", "description": "Created by test suite"})
    response = requests.get(url="http://localhost:8000/setups/list").json()
    setup_identifier = response["data"][0]["id"]

    # Activate setup.
    requests.post(url="http://localhost:8000/activate", json={"id": setup_identifier})

    # Deactivate setup.
    requests.post(url="http://localhost:8000/deactivate", json={"id": setup_identifier})

    # Remove the setup again.
    requests.post(url="http://localhost:8000/setups/delete", json={"id": setup_identifier})

    # Read application log.
    application_log = webinterface_service.read_log()

    # Verify everything is in place.
    assert "Activating setup id=1" in application_log
    assert """Publishing message: {'exchange': 'secpi', 'routing_key': 'secpi-on_off', 'body': '{"setup_name": "secpi-testing", "active_state": true}'}""" in application_log
    assert """Action successful: SuccessfulResponse(message="Activating setup 'secpi-testing' succeeded")""" in application_log

    assert "Deactivating setup id=1" in application_log
    assert """Publishing message: {'exchange': 'secpi', 'routing_key': 'secpi-on_off', 'body': '{"setup_name": "secpi-testing", "active_state": false}'}""" in application_log
    assert """Action successful: SuccessfulResponse(message="Deactivating setup 'secpi-testing' succeeded")""" in application_log

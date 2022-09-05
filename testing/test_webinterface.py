import logging
import time

import requests

from secpi import __version__
from testing.util.service import WebinterfaceServiceWrapper

logger = logging.getLogger(__name__)


def test_webinterface_start_stop():
    """
    Start Webinterface and immediately shut it down again. Verify that the log output matches the expectations.
    """

    # Start service in separate process.
    service = WebinterfaceServiceWrapper()
    service.run()

    # Before shutting down, wait a bit so that we can receive the whole log.
    time.sleep(0.25)

    # Send service a shutdown signal.
    service.shutdown()

    # Read application log.
    app_log = service.read_log()

    # Verify everything is in place.
    assert "Configuring Webinterface" in app_log
    assert "Using template path" in app_log
    assert "Loading configuration from etc/testing/config-web.toml" in app_log
    assert "Connecting to database sqlite:///secpi-database-testing.sqlite" in app_log
    assert "Initializing Webserver" in app_log
    assert "Connecting to AMQP broker <URLParameters host=localhost port=5672 virtual_host=/ ssl=False>" in app_log
    assert "Connecting to AMQP broker successful" in app_log
    assert "AMQP: Connected to broker" in app_log

    # TODO: Occasionally missing?
    assert "Serving on http://0.0.0.0:8000" in app_log
    assert "ENGINE Bus STARTED" in app_log

    assert "Got message on operational endpoint: {'action': 'shutdown'}" in app_log
    assert "Shutting down" in app_log
    assert "Stop consuming AMQP queue" in app_log
    assert "ENGINE Bus STOPPING" in app_log
    assert "ENGINE Bus EXITED" in app_log


def test_webinterface_with_activate(webinterface_service):
    """
    Start Webinterface, create, activate, and deactivate setup. Verify that the log output matches the expectations.
    """

    # Create a setup.
    requests.post(
        url="http://localhost:8000/setups/add", json={"name": "secpi-testing", "description": "Created by test suite"}
    )
    response = requests.get(url="http://localhost:8000/setups/list").json()
    setup_identifier = response["data"][0]["id"]

    # Activate setup.
    requests.post(url="http://localhost:8000/activate", json={"id": setup_identifier})

    # Deactivate setup.
    requests.post(url="http://localhost:8000/deactivate", json={"id": setup_identifier})

    # Remove the setup again.
    requests.post(url="http://localhost:8000/setups/delete", json={"id": setup_identifier})

    # Read application log.
    app_log = webinterface_service.read_log()

    # Verify everything is in place.
    assert "Activating setup id=1" in app_log
    assert (
        """Publishing message. queue=secpi-on_off, message={'setup_name': 'secpi-testing', 'active_state': True}"""
        in app_log
    )
    assert (
        """Activate/deactivate successful: SuccessfulResponse(message="Activating setup 'secpi-testing' succeeded")"""
        in app_log
    )

    assert "Deactivating setup id=1" in app_log
    assert (
        """Publishing message. queue=secpi-on_off, message={'setup_name': 'secpi-testing', 'active_state': False}"""
        in app_log
    )
    assert (
        """Activate/deactivate successful: SuccessfulResponse(message="Deactivating setup 'secpi-testing' succeeded")"""
        in app_log
    )


def test_webinterface_version_in_footer(webinterface_service):
    """
    Verify that the current software version is reflected in the website footer.
    """
    response = requests.get(url="http://localhost:8000/")
    assert f"Version {__version__}" in response.text

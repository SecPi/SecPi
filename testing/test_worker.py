import json
import logging
import subprocess
import time

from testing.util.events import get_action_event
from testing.util.service import WorkerServiceWrapper

logger = logging.getLogger(__name__)


def test_worker_start_stop():
    """
    Start Worker and immediately shut it down again. Verify that the log output matches the expectations.
    """

    # Start service in separate process.
    service = WorkerServiceWrapper()
    service.run()

    # Send service a shutdown signal.
    service.shutdown(identifier="1")

    # Read application log.
    app_log = service.read_log()

    # Verify everything is in place.
    assert "Loading configuration from etc/testing/config-worker.toml" in app_log
    assert "Connecting to AMQP broker <URLParameters host=localhost port=5672 virtual_host=/ ssl=False>" in app_log
    assert "Connecting to AMQP broker successful" in app_log
    assert "Setting up sensors and actions" in app_log
    assert "Start consuming AMQP queue" in app_log
    assert """Got message on operational channel: b\'{"action": "shutdown"}""" in app_log

    assert "Test Action cleanup" in app_log
    assert "TCPPortListener: Sensor deactivated successfully, id=1" in app_log
    assert "Removed action: 1" in app_log
    assert "Removed sensor: 1" in app_log

    assert "Stop consuming AMQP queue" in app_log
    assert "Disconnecting" in app_log
    assert "Deleting service instance" in app_log


def test_worker_with_tcplistener(worker_service):
    """
    Start Worker and submit a sensor trigger using TCP. Verify that the log output matches the expectations.
    """

    # Give system some time for making sure the TCP listener has started.
    # TODO: Wait polling.
    time.sleep(0.25)

    # Submit a sensor signal.
    command = "echo hello | socat - tcp:localhost:1234"
    subprocess.check_output(command, shell=True)

    # Give system some time for processing.
    time.sleep(0.15)

    # Read application log.
    app_log = worker_service.read_log()

    # Verify everything is in place.
    assert "Loading class successful: secpi.sensor.network.TCPPortListener" in app_log
    assert "Sensor with id 1 detected something" in app_log
    assert (
        "Publishing message:" in app_log
        and '"sensor_id": 1, "worker_id": 1, "message": "Got TCP connection, raising alarm"' in app_log
    )


def test_worker_with_testaction(worker_service):
    """
    Start Worker and submit an action signal using AMQP. Verify that the log output matches the expectations.
    """

    # Emulate an action signal using AMQP.
    command = f"""echo '{json.dumps(get_action_event())}' | amqp-publish --routing-key=secpi-action-1"""
    subprocess.check_output(command, shell=True)

    # Give system some time for processing.
    time.sleep(0.25)

    # Read application log.
    app_log = worker_service.read_log()

    # Verify everything is in place.
    assert "Loading class successful: secpi.action.test.TestAction" in app_log
    assert "Test Action initialized" in app_log

    assert "Registering action: 1" in app_log
    assert "Registered action: {'id': 1" in app_log
    # assert "Registering action: 2" in app_log
    # assert "Registered action: {'id': 2" in app_log
    assert "Setup of sensors and actions completed" in app_log
    assert "Executing Test Action" in app_log

    assert "Test Action message: foobar" in app_log
    assert "Creating file artefacts in memory" in app_log
    assert "Created ZIP file" in app_log
    assert "Publishing message: {'exchange': 'secpi', 'routing_key': 'secpi-action-response'" in app_log
    assert "Sent data to manager" in app_log

    # assert "Test Action message: bazqux" in app_log
    # assert "No data to zip" in app_log
    # assert "No data to send" in app_log

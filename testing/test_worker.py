import logging
import subprocess
import time

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
    assert "Loading configuration from testing/etc/config-worker.json" in app_log
    assert "Connecting to AMQP broker at localhost:5672" in app_log
    assert "Setting up sensors and actions" in app_log
    assert "Start consuming AMQP queue" in app_log
    assert """Got message on operational channel: b\'{"action": "shutdown"}""" in app_log
    assert "Stop consuming AMQP queue" in app_log


def test_worker_with_tcplistener(worker_service):
    """
    Start Worker and submit a sensor trigger using TCP. Verify that the log output matches the expectations.
    """

    # Give system some time for making sure the TCP listener has started.
    # FIXME: Wait polling.
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
        "Publishing message:" in app_log and '"sensor_id": 1, "message": "Got TCP connection, raising alarm"' in app_log
    )

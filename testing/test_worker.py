import logging
import subprocess
import time

from testing.util.service import ServiceWrapper

logger = logging.getLogger(__name__)


def test_worker_start_stop():
    """
    Start Worker and immediately shut it down again. Verify that the log output matches the expectations.
    """

    # Start Worker in separate process.
    service = ServiceWrapper()
    service.run_worker()

    # Send Worker a shutdown signal.
    service.shutdown(identifier="1")

    # Read application log.
    application_log = service.read_log()

    # Verify everything is in place.
    assert "Loading configuration from testing/etc/config-worker.json" in application_log
    assert "Connecting to AMQP broker at localhost:5672" in application_log
    assert "Setting up sensors and actions" in application_log
    assert "Loading class successful: worker.tcpportlistener.TCPPortListener" in application_log
    assert "Start consuming AMQP queue" in application_log
    assert """Got message on operational channel: b\'{"action": "shutdown"}""" in application_log
    assert "Stop consuming AMQP queue" in application_log
    assert "Disconnected from RabbitMQ" in application_log


def test_worker_with_tcplistener(worker_service):
    """
    Start Worker and submit a sensor trigger using TCP. Verify that the log output matches the expectations.
    """

    # Submit a sensor signal.
    command = "echo hello | socat - tcp:localhost:1234"
    subprocess.check_output(command, shell=True)

    # Give system some time for processing.
    time.sleep(0.25)

    # Read application log.
    application_log = worker_service.read_log()

    # Verify everything is in place.
    assert "Sensor with id 1 detected something" in application_log
    assert \
        "Publishing message:" in application_log and \
        '"sensor_id": 1, "message": "Got TCP connection, raising alarm"' in application_log

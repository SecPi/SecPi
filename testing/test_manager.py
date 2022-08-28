import json
import logging
import subprocess
import time

from testing.util.service import ServiceWrapper

logger = logging.getLogger(__name__)


def test_manager_start_stop():
    """
    Start Manager and immediately shut it down again. Verify that the log output matches the expectations.
    """

    # Start Worker in separate process.
    service = ServiceWrapper()
    service.run_manager()

    # Send Worker a shutdown signal.
    service.shutdown(identifier="m")

    # Read application log.
    application_log = service.read_log()

    # Verify everything is in place.
    assert "Loading configuration from testing/etc/config-manager.json" in application_log
    assert "Storing alarms to" in application_log
    assert "Connecting to database sqlite:///secpi-database-test.sqlite" in application_log
    assert "Connecting to AMQP broker at localhost:5672" in application_log
    assert "Manager is ready" in application_log
    assert "Start consuming AMQP queue" in application_log
    assert """Got message on operational channel: b\'{"action": "shutdown"}""" in application_log
    assert "Stop consuming AMQP queue" in application_log
    assert "Disconnected from RabbitMQ" in application_log


def test_manager_with_alarm(manager_service):
    """
    Start Manager and submit an alarm using AMQP. Verify that the log output matches the expectations.
    """

    # Submit an alarm signal.
    data = {"pi_id": 1, "sensor_id": 1, "message": "Got TCP connection, raising alarm", "datetime": "2022-08-27 02:33:33"}
    payload = json.dumps(data)
    command = f"""echo '{payload}' | amqp-publish --routing-key=secpi-alarm"""
    subprocess.check_output(command, shell=True)

    # Give system some time for processing.
    time.sleep(0.35)

    # Read application log.
    application_log = manager_service.read_log()

    # Verify everything is in place.
    assert \
        "Received old alarm:" in application_log and \
        '"sensor_id": 1, "message": "Got TCP connection, raising alarm"' in application_log
    assert "Created directory for alarm:" in application_log
    assert "Old alarm from 1 on sensor 1: Got TCP connection, raising alarm" in application_log
    assert "Received all data from workers, cancelling the timeout" in application_log

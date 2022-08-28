import json
import logging
import subprocess
import time

from testing.util.service import ManagerServiceWrapper

logger = logging.getLogger(__name__)


def test_manager_start_stop():
    """
    Start Manager and immediately shut it down again. Verify that the log output matches the expectations.
    """

    # Start service in separate process.
    service = ManagerServiceWrapper()
    service.run()

    # Send service a shutdown signal.
    service.shutdown(identifier="m")

    # Read application log.
    app_log = service.read_log()

    # Verify everything is in place.


def test_manager_with_alarm(manager_service):
    assert "Loading configuration from testing/etc/config-manager.json" in app_log
    assert "Storing alarms to" in app_log
    assert "Connecting to database sqlite:///secpi-database-testing.sqlite" in app_log
    assert "Connecting to AMQP broker at localhost:5672" in app_log
    assert "Manager is ready" in app_log
    assert "Start consuming AMQP queue" in app_log
    assert """Got message on operational channel: b\'{"action": "shutdown"}""" in app_log
    assert "Stop consuming AMQP queue" in app_log
    assert "Disconnected from RabbitMQ" in app_log
    """
    Start Manager and submit an alarm using AMQP. Verify that the log output matches the expectations.
    """

    # Submit an alarm signal.
    data = {"pi_id": 1, "sensor_id": 1, "message": "Got TCP connection, raising alarm", "datetime": "2022-08-27 02:33:33"}
    payload = json.dumps(data)
    command = f"""echo '{payload}' | amqp-publish --routing-key=secpi-alarm"""
    subprocess.check_output(command, shell=True)

    # Give system some time for processing.
    time.sleep(0.45)

    # Read application log.
    app_log = manager_service.read_log()

    # Verify everything is in place.
    assert \
        "Received old alarm:" in app_log and \
        '"sensor_id": 1, "message": "Got TCP connection, raising alarm"' in app_log
    assert "Created directory for alarm:" in app_log
    assert "Old alarm from 1 on sensor 1: Got TCP connection, raising alarm" in app_log
    assert "Received all data from workers, cancelling the timeout" in app_log

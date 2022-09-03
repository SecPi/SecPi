import json
import logging
import subprocess
import time

from testing.util.events import OLD_ALARM_EVENT
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
    assert "Loading configuration from etc/testing/config-manager.json" in app_log
    assert "Storing alarms to" in app_log
    assert "Connecting to database sqlite:///secpi-database-testing.sqlite" in app_log
    assert "Connecting to AMQP broker at localhost:5672" in app_log
    assert "Manager is ready" in app_log
    assert "Start consuming AMQP queue" in app_log
    assert """Got message on operational channel: b\'{"action": "shutdown"}""" in app_log
    assert "Stop consuming AMQP queue" in app_log


def test_manager_receive_alarm(manager_service):
    """
    Start Manager and submit an alarm event using AMQP. Verify that the log output matches the expectations.
    """

    # Submit an alarm signal.
    command = f"""echo '{json.dumps(OLD_ALARM_EVENT)}' | amqp-publish --routing-key=secpi-alarm"""
    subprocess.check_output(command, shell=True)

    # Give system some time for processing.
    time.sleep(0.55)

    # Read application log.
    app_log = manager_service.read_log()

    # Verify everything is in place.
    assert (
        "Received late alarm:" in app_log
        and '"sensor_id": 1, "message": "Got TCP connection, raising alarm"' in app_log
    )
    assert "Created directory for alarm:" in app_log
    assert "[LATE] Alarm from sensor id=1, worker id=1: Got TCP connection, raising alarm" in app_log
    assert "Received all data from workers, cancelling the timeout" in app_log

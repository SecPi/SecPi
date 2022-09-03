import json
import subprocess
import time

import requests

from testing.util.events import OLD_ALARM_EVENT

WORKER_ENTITY = {"id": 1, "name": "worker-testing", "address": "localhost"}

NOTIFIER_ENTITY = {"id": 1, "name": "mailer-testing", "module": "mailer", "cl": "Mailer", "active_state": True}
NOTIFIER_PARAMS = [
    {"object_id": 1, "object_type": "notifier", "key": "smtp_address", "value": "localhost"},
    {"object_id": 1, "object_type": "notifier", "key": "smtp_port", "value": "12525"},
    {"object_id": 1, "object_type": "notifier", "key": "smtp_user", "value": ""},
    {"object_id": 1, "object_type": "notifier", "key": "smtp_pass", "value": ""},
    {"object_id": 1, "object_type": "notifier", "key": "smtp_security", "value": "NOAUTH_NOSSL"},
    {"object_id": 1, "object_type": "notifier", "key": "sender", "value": "secpi@example.org"},
    {"object_id": 1, "object_type": "notifier", "key": "recipient", "value": "user@example.org"},
    {"object_id": 1, "object_type": "notifier", "key": "subject", "value": "SecPi Alarm"},
    {"object_id": 1, "object_type": "notifier", "key": "text", "value": "Your SecPi raised an alarm"},
    {"object_id": 1, "object_type": "notifier", "key": "unzip_attachments", "value": "1"},
]

ACTION_ENTITY = {"id": 1, "name": "action-testing", "module": "test", "cl": "TestAction", "active_state": True}
ACTION_PARAMS = [
    {"object_id": 1, "object_type": "action", "key": "msg", "value": "foobar"},
]
ACTION_WORKER_ENTITY = {"action_id": 1, "worker_id": 1}


def create_and_activate_setup(with_notifier=False, with_worker=False, with_action=False):

    # Create a setup.
    requests.post(
        url="http://localhost:8000/setups/add", json={"name": "secpi-testing", "description": "Created by test suite"}
    )
    response = requests.get(url="http://localhost:8000/setups/list").json()
    setup_identifier = response["data"][0]["id"]

    # Optionally create notifier items.
    if with_notifier:
        requests.post(url="http://localhost:8000/notifiers/add", json=NOTIFIER_ENTITY)
        for param in NOTIFIER_PARAMS:
            requests.post(url="http://localhost:8000/notifierparams/add", json=param)

    # Optionally create worker items.
    if with_worker:
        requests.post(url="http://localhost:8000/workers/add", json=WORKER_ENTITY)

    # Optionally create action items.
    if with_action:
        requests.post(url="http://localhost:8000/actions/add", json=ACTION_ENTITY)
        for param in ACTION_PARAMS:
            requests.post(url="http://localhost:8000/actionparams/add", json=param)
        requests.post(url="http://localhost:8000/workersactions/add", json=ACTION_WORKER_ENTITY)

    # Activate setup.
    requests.post(url="http://localhost:8000/activate", json={"id": setup_identifier})


def test_manager_process_alarm(webinterface_service, manager_service):
    """
    Start Manager, register the `mailer.Mailer` notifier, and submit a corresponding alarm event using AMQP.

    This is a half-stack test, at least a full round-trip for the Manager service.
    Verify that the log output matches the expectations.
    """

    create_and_activate_setup(with_notifier=True)

    # Emulate an alarm signal using AMQP.
    command = f"""echo '{json.dumps(OLD_ALARM_EVENT)}' | amqp-publish --routing-key=secpi-alarm"""
    subprocess.check_output(command, shell=True)

    # Give system some time for processing.
    time.sleep(0.50)

    # Read application log.
    web_log = webinterface_service.read_log()
    app_log = manager_service.read_log()

    # Verify everything is in place.

    # Setup: Webinterface.
    assert "Activating setup id=1" in web_log
    assert (
        """Publishing message. queue=secpi-on_off, message={'setup_name': 'secpi-testing', 'active_state': True}"""
        in web_log
    )
    assert (
        """Activate/deactivate successful: SuccessfulResponse(message="Activating setup 'secpi-testing' succeeded")"""
        in web_log
    )

    # Setup: Manager.
    assert "Setting up notifiers" in app_log
    assert "Loading class successful: secpi.notifier.mailer.Mailer" in app_log
    assert "Mailer: Notifier initialized" in app_log
    assert "Set up notifier Mailer" in app_log
    assert "Activating setup: secpi-testing" in app_log

    # Alarm event.
    assert (
        "Received late alarm:" in app_log
        and '"sensor_id": 1, "message": "Got TCP connection, raising alarm"' in app_log
    )
    assert "Created directory for alarm:" in app_log
    assert "[LATE] Alarm from sensor id=1, worker id=1: Got TCP connection, raising alarm" in app_log
    # assert "Received all data from workers, cancelling the timeout" in app_log

    # Notification.
    assert "Notifying via SMTP email" in app_log
    # assert "Failed to prepare email attachments" in app_log
    # assert "Mailer: Will look into" in app_log
    assert "Mailer: Trying to send mail without authentication" in app_log
    assert "Mailer: Establishing connection to SMTP server" in app_log
    assert "Mailer: Unexpected error"
    assert (
        "ConnectionRefusedError: [Errno 61] Connection refused" in app_log
        or "ConnectionRefusedError: [Errno 111] Connection refused" in app_log
        or "OSError: [Errno 99] Cannot assign requested address" in app_log
    )

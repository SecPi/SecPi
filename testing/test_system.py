import json
import subprocess
import time
from email.message import Message

import requests

from testing.util.events import OLD_ALARM_EVENT

WORKER_ENTITY = {"id": 1, "name": "worker-testing", "address": "localhost"}

NOTIFIER_ENTITY = {"id": 1, "name": "mailer-testing", "module": "mailer", "cl": "Mailer", "active_state": True}
NOTIFIER_PARAMS = [
    {"object_id": 1, "object_type": "notifier", "key": "smtp_address", "value": "localhost"},
    {"object_id": 1, "object_type": "notifier", "key": "smtp_port", "value": "8025"},
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
    """
    Populate the database, using the HTTP API.
    """

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

    # Populate database, using the HTTP API.
    create_and_activate_setup(with_notifier=True)

    # Emulate an alarm signal using AMQP.
    command = f"""echo '{json.dumps(OLD_ALARM_EVENT)}' | amqp-publish --routing-key=secpi-alarm"""
    subprocess.check_output(command, shell=True)

    # Give system some time for processing.
    time.sleep(0.05)

    # Emulate an action response signal using AMQP.
    command = """echo '__NODATA__' | amqp-publish --routing-key=secpi-action-response"""
    subprocess.check_output(command, shell=True)

    # Give system some time for processing.
    time.sleep(0.25)

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
    # assert "Created directory for alarm:" in app_log
    assert "[LATE] Alarm from sensor id=1, worker id=1: Got TCP connection, raising alarm" in app_log

    assert "Executing actions" in app_log
    assert "Starting to wait for action response from worker" in app_log
    assert "Waiting for action response from worker"
    assert "Received response from action invocation" in app_log
    assert "Received empty action response from worker" in app_log

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


def test_full_stack(manager_service, worker_service, webinterface_service, smtpd):
    """
    Start the full stack and invoke an alarm signal.
    Verify that the sensor triggered and all notifiers and actions have been invoked correctly.
    """

    # Populate database, using the HTTP API.
    create_and_activate_setup(with_worker=True, with_notifier=True, with_action=True)

    # Submit a sensor signal using TCP.
    command = "echo hello | socat - tcp:localhost:1234"
    subprocess.check_output(command, shell=True)

    # Give system some time for processing.
    time.sleep(0.50)

    # Read application log.
    manager_log = manager_service.read_log()
    worker_log = worker_service.read_log()

    # Verify everything is in place.
    assert "Loading class successful: secpi.action.test.TestAction" in worker_log
    assert "Test Action initialized" in worker_log

    assert "Registering action: 1" in worker_log
    assert "Registered action: {'id': 1" in worker_log
    # assert "Registering action: 2" in app_log
    # assert "Registered action: {'id': 2" in app_log
    assert "Setup of sensors and actions completed" in worker_log

    assert "Alarm from sensor id=1, worker worker-testing: Got TCP connection, raising alarm" in manager_log
    # assert "Created directory for alarm:" in manager_log
    assert "Executing actions" in manager_log

    assert "Executing Test Action" in worker_log

    assert "Test Action message: foobar" in worker_log
    assert "Creating file artefacts in memory" in worker_log
    assert "Created ZIP file" in worker_log
    assert "Publishing message: {'exchange': 'secpi', 'routing_key': 'secpi-action-response'" in worker_log
    assert "Sent data to manager" in worker_log

    assert "Got log message from Worker 1: Executing Test Action" in manager_log
    assert "Got log message from Worker 1: Test Action message: foobar" in manager_log
    assert "Received response from action invocation" in manager_log
    # assert re.match(r".*Writing data to current alarm dir:.*\.zip", manager_log, re.DOTALL | re.MULTILINE)

    assert "Received action response from worker" in manager_log
    assert "Notifying via SMTP email" in manager_log

    assert "Mailer: Attached file 'index.txt' to message" in manager_log
    assert "Mailer: Attached file 'index.json' to message" in manager_log
    assert "Mailer: Attached file 'index.xml' to message" in manager_log

    assert "Mailer: Trying to send mail without authentication" in manager_log
    assert "Mailer: Establishing connection to SMTP server" in manager_log

    assert len(smtpd.messages) == 1

    message: Message = smtpd.messages[0]

    assert message.is_multipart()
    assert message.get("From") == "secpi@example.org"
    assert message.get("To") == "user@example.org"
    assert message.get("Subject") == "SecPi Alarm"

    parts = []
    for message in message.get_payload():
        part = dict(
            body=message.get_payload().strip(),
            type=message.get("Content-Type"),
            disposition=message.get("Content-Disposition"),
        )
        parts.append(part)
    assert (
        dict(body="WW91ciBTZWNQaSByYWlzZWQgYW4gYWxhcm0=", type='text/plain; charset="utf-8"', disposition=None) in parts
    )
    assert (
        dict(
            body="Received alarm on sensor id=1 from worker worker-testing: Got TCP connection, raising alarm",
            type='text/plain; charset="us-ascii"',
            disposition=None,
        )
        in parts
    )

    attachments = sorted([part["disposition"] for part in parts if part["disposition"]])
    assert len(attachments) == 5
    assert 'attachment; filename="index.json"' in attachments
    assert 'attachment; filename="index.txt"' in attachments
    assert 'attachment; filename="index.xml"' in attachments

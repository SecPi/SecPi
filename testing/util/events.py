import time

OLD_ALARM_EVENT = {
    "worker_id": 1,
    "sensor_id": 1,
    "message": "Got TCP connection, raising alarm",
    "datetime": "2022-08-27 02:33:33",
}

WORKER_ENTITY = {"id": 1, "name": "worker-testing", "address": "localhost"}

NOTIFIER_ENTITY = {"id": 1, "name": "mailer-testing", "module": "mailer", "cl": "Mailer", "active_state": True}
NOTIFIER_PARAMS = [
    {"notifier_id": 1, "object_type": "notifier", "key": "smtp_address", "value": "localhost"},
    {"notifier_id": 1, "object_type": "notifier", "key": "smtp_port", "value": "8025"},
    {"notifier_id": 1, "object_type": "notifier", "key": "smtp_user", "value": ""},
    {"notifier_id": 1, "object_type": "notifier", "key": "smtp_pass", "value": ""},
    {"notifier_id": 1, "object_type": "notifier", "key": "smtp_security", "value": "NOAUTH_NOSSL"},
    {"notifier_id": 1, "object_type": "notifier", "key": "sender", "value": "secpi@example.org"},
    {"notifier_id": 1, "object_type": "notifier", "key": "recipient", "value": "user@example.org"},
    {"notifier_id": 1, "object_type": "notifier", "key": "subject", "value": "SecPi Alarm"},
    {"notifier_id": 1, "object_type": "notifier", "key": "text", "value": "Your SecPi raised an alarm"},
    {"notifier_id": 1, "object_type": "notifier", "key": "unzip_attachments", "value": "1"},
]

ACTION_ENTITY = {"id": 1, "name": "action-testing", "module": "test", "cl": "TestAction", "active_state": True}
ACTION_PARAMS = [
    {"action_id": 1, "object_type": "action", "key": "msg", "value": "foobar"},
]
ACTION_WORKER_ENTITY = {"action_id": 1, "worker_id": 1}

def get_action_event():
    return {
        "msg": "execute",
        "datetime": time.strftime("%Y-%m-%d %H:%M:%S"),
        "alarm": OLD_ALARM_EVENT,
    }

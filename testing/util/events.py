import time

OLD_ALARM_EVENT = {
    "worker_id": 1,
    "sensor_id": 1,
    "message": "Got TCP connection, raising alarm",
    "datetime": "2022-08-27 02:33:33",
}


def get_action_event():
    return {
        "msg": "execute",
        "datetime": time.strftime("%Y-%m-%d %H:%M:%S"),
        "alarm": OLD_ALARM_EVENT,
    }

from unittest.mock import call

import pytest

from tools.sensor import Sensor
from tools.utils import load_class


@pytest.fixture(scope="function")
def pinger_sensor(worker_mock) -> Sensor:
    """
    Provide the test cases with a `Pinger` instance, where its Worker is mocked.
    """

    # Configure sensor.
    component = load_class("worker.pinger", "Pinger")
    parameters = {
        "destination_ip": "9.9.9.9",
        "interval": "0.05",
        "max_losses": "0",
        "bounce_time": "0",
    }

    # Create sensor instance.
    sensor: Sensor = component(id=99, params=parameters, worker=worker_mock)

    yield sensor


def test_sensor_pinger_alarm(pinger_sensor, caplog):
    """
    Test the alarm method of the `Pinger`. No sensor logic involved.
    """

    # Invoke alarm, without actually triggering the sensor logic.
    pinger_sensor.activate()
    pinger_sensor.alarm("Hello, world.")
    pinger_sensor.deactivate()

    # Verify the right calls would have been made to the Worker.
    assert pinger_sensor.worker.mock_calls == [
        call.post_log('Pinger: Sensor activated successfully, id=99', 50),
        call.alarm(99, 'Hello, world.'),
        call.post_log('Pinger: Sensor deactivated successfully, id=99', 50)
    ]

    setup_tuples = [(r.name, r.levelno, r.getMessage()) for r in caplog.get_records(when="setup")]
    assert setup_tuples == [
        ('tools.utils', 20, 'Loading class successful: worker.pinger.Pinger'),
        ('worker.pinger', 20, "Initializing sensor id=99 with parameters {'destination_ip': '9.9.9.9', 'interval': '0.05', 'max_losses': '0', 'bounce_time': '0'}"),
        ('worker.pinger', 10, "Pinger: Sensor initialized"),
    ]

    assert caplog.record_tuples == [
        ("tools.sensor", 20, "Pinger: Sensor activated successfully, id=99"),
        ("tools.sensor", 20, "Pinger: Sensor deactivated successfully, id=99"),
    ]

    # Verify log output matches the expectations.
    setup_messages = [r.getMessage() for r in caplog.get_records(when="setup")]
    assert "Loading class successful: worker.pinger.Pinger" in setup_messages
    assert "Initializing sensor id=99 with parameters {'destination_ip': '9.9.9.9', 'interval': '0.05', 'max_losses': '0', 'bounce_time': '0'}" in setup_messages
    assert "Pinger: Sensor activated successfully, id=99" in caplog.messages
    assert "Pinger: Sensor deactivated successfully, id=99" in caplog.messages

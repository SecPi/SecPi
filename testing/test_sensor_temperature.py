from unittest.mock import call

import pytest

from tools.sensor import Sensor
from tools.utils import load_class


@pytest.fixture()
def fake_device(fs_session):
    yield fs_session.create_file("/sys/bus/w1/devices/foobar/w1_slave", contents="foo\nbar")


@pytest.fixture(scope="function")
def temperature_sensor(fake_device, worker_mock) -> Sensor:
    """
    Provide the test cases with a `TemperatureSensor` instance, where its Worker is mocked.
    """

    # Configure sensor.
    component = load_class("worker.temperature_sensor", "TemperatureSensor")
    parameters = {
        "device_id": "foobar",
        "bouncetime": "3",
        "min": "3",
        "max": "60",
    }

    # Create sensor instance.
    sensor: Sensor = component(id=99, params=parameters, worker=worker_mock)

    yield sensor


def test_sensor_temperature_alarm(fake_device, temperature_sensor, caplog):
    """
    Test the alarm method of the `TemperatureSensor`. No sensor logic involved.
    """

    # Invoke alarm, without actually triggering the sensor logic.
    temperature_sensor.activate()
    temperature_sensor.alarm("Hello, world.")
    temperature_sensor.deactivate()

    # Verify the right calls would have been made to the Worker.
    assert temperature_sensor.worker.mock_calls == [
        call.post_log('TemperatureSensor: Sensor activated successfully, id=99', 50),
        call.alarm(99, 'Hello, world.'),
        call.post_log('TemperatureSensor: Sensor deactivated successfully, id=99', 50)
    ]

    setup_tuples = [(r.name, r.levelno, r.getMessage()) for r in caplog.get_records(when="setup")]
    assert setup_tuples == [
        ('tools.utils', 20, 'Loading class successful: worker.temperature_sensor.TemperatureSensor'),
        ('worker.temperature_sensor', 20, "Initializing sensor id=99 with parameters {'device_id': 'foobar', 'bouncetime': '3', 'min': '3', 'max': '60'}"),
        ('worker.temperature_sensor', 20, "TemperatureSensor: Sensor initialized"),
    ]

    assert caplog.record_tuples == [
        ("tools.sensor", 20, "TemperatureSensor: Sensor activated successfully, id=99"),
        ("tools.sensor", 20, "TemperatureSensor: Sensor deactivated successfully, id=99"),
    ]

    # Verify log output matches the expectations.
    setup_messages = [r.getMessage() for r in caplog.get_records(when="setup")]
    assert "Loading class successful: worker.temperature_sensor.TemperatureSensor" in setup_messages
    assert "Initializing sensor id=99 with parameters {'device_id': 'foobar', 'bouncetime': '3', 'min': '3', 'max': '60'}" in setup_messages
    assert "TemperatureSensor: Sensor activated successfully, id=99" in caplog.messages
    assert "TemperatureSensor: Sensor deactivated successfully, id=99" in caplog.messages

from unittest.mock import call

import pytest

from secpi.model.sensor import Sensor
from secpi.util.common import load_class


@pytest.fixture
def fake_device(fs):
    yield fs.create_file("/sys/bus/w1/devices/foobar/w1_slave", contents="foo\nbar")


@pytest.fixture(scope="function")
def system_temperature_sensor(fake_device, worker_mock) -> Sensor:
    """
    Provide the test cases with a `SystemTemperature` instance, where its Worker is mocked.
    """

    # Configure sensor.
    component = load_class("secpi.sensor.system", "SystemTemperature")
    parameters = {
        "device_id": "foobar",
        "bouncetime": "3",
        "min": "3",
        "max": "60",
    }

    # Create sensor instance.
    sensor: Sensor = component(id=99, params=parameters, worker=worker_mock)

    yield sensor


def test_sensor_temperature_alarm(system_temperature_sensor, caplog):
    """
    Test the alarm method of the `SystemTemperature`. No sensor logic involved.
    """

    # Invoke alarm, without actually triggering the sensor logic.
    system_temperature_sensor.activate()
    system_temperature_sensor.alarm("Hello, world.")
    system_temperature_sensor.deactivate()

    # Verify the right calls would have been made to the Worker.
    assert system_temperature_sensor.worker.mock_calls == [
        call.post_log("SystemTemperature: Sensor activated successfully, id=99", 50),
        call.alarm(99, "Hello, world."),
        call.post_log("SystemTemperature: Sensor deactivated successfully, id=99", 50),
    ]

    # Verify log output matches the expectations.
    setup_tuples = [(r.name, r.levelno, r.getMessage()) for r in caplog.get_records(when="setup")]
    assert setup_tuples == [
        ("secpi.util.common", 20, "Loading class successful: secpi.sensor.system.SystemTemperature"),
        (
            "secpi.sensor.system",
            20,
            "Initializing sensor id=99 with parameters "
            "{'device_id': 'foobar', 'bouncetime': '3', 'min': '3', 'max': '60'}",
        ),
        ("secpi.sensor.system", 20, "SystemTemperature: Sensor initialized"),
    ]

    # This sensor does not send anything to the log by default.
    assert caplog.record_tuples == []

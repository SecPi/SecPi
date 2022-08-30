from unittest.mock import call

import pytest
from surrogate import surrogate

from tools.sensor import Sensor
from tools.utils import load_class


@pytest.fixture(scope="function")
def gpio_sensor(worker_mock, mocker) -> Sensor:
    """
    Provide the test cases with a `GPIOSensor` instance, where its Worker is mocked.
    """

    # Configure sensor.
    with surrogate("RPi.GPIO"):
        mocker.patch("RPi.GPIO")
        component = load_class("worker.gpio_sensor", "GPIOSensor")
    parameters = {
        "gpio": "42",
        "bouncetime": "3",
    }

    # Create sensor instance.
    sensor: Sensor = component(id=99, params=parameters, worker=worker_mock)

    yield sensor


def test_gpio_load_fails():
    """
    Because `RPi.GPIO` is not installed, loading the `GPIOSensor` should croak.
    """
    with pytest.raises(ModuleNotFoundError) as ex:
        load_class("worker.gpio_sensor", "GPIOSensor")
    assert ex.match("No module named 'RPi'")


def test_sensor_gpio_alarm(gpio_sensor, caplog):
    """
    Test the alarm method of the `GPIOSensor`. No sensor logic involved.
    """

    # Invoke alarm, without actually triggering the sensor logic.
    gpio_sensor.activate()
    gpio_sensor.alarm("Hello, world.")
    gpio_sensor.deactivate()

    # Verify the right calls would have been made to the Worker.
    assert gpio_sensor.worker.mock_calls == [
        call.post_log('GPIOSensor: Sensor activated successfully, id=99', 50),
        call.alarm(99, 'Hello, world.'),
        call.post_log('GPIOSensor: Sensor deactivated successfully, id=99', 50)
    ]

    setup_tuples = [(r.name, r.levelno, r.getMessage()) for r in caplog.get_records(when="setup")]
    assert setup_tuples == [
        ('tools.utils', 20, 'Loading class successful: worker.gpio_sensor.GPIOSensor'),
        ('worker.gpio_sensor', 20, "Initializing sensor id=99 with parameters {'gpio': '42', 'bouncetime': '3'}"),
        ('worker.gpio_sensor', 10, "GPIOSensor: Sensor initialized"),
    ]

    assert caplog.record_tuples == [
        ("worker.gpio_sensor", 10, "GPIOSensor: Registered sensor at pin 42"),
        ("tools.sensor", 20, "GPIOSensor: Sensor activated successfully, id=99"),
        ("worker.gpio_sensor", 10, "GPIOSensor: Removed sensor at pin 42"),
        ("tools.sensor", 20, "GPIOSensor: Sensor deactivated successfully, id=99"),
    ]

    # Verify log output matches the expectations.
    setup_messages = [r.getMessage() for r in caplog.get_records(when="setup")]
    assert "Loading class successful: worker.gpio_sensor.GPIOSensor" in setup_messages
    assert "Initializing sensor id=99 with parameters {'gpio': '42', 'bouncetime': '3'}" in setup_messages
    assert "GPIOSensor: Registered sensor at pin 42" in caplog.messages
    assert "GPIOSensor: Sensor activated successfully, id=99" in caplog.messages
    assert "GPIOSensor: Removed sensor at pin 42" in caplog.messages
    assert "GPIOSensor: Sensor deactivated successfully, id=99" in caplog.messages

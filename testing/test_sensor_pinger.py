from unittest.mock import call

import pytest

from secpi.model.sensor import Sensor
from secpi.util.common import load_class


@pytest.fixture(scope="function")
def pinger_sensor(worker_mock) -> Sensor:
    """
    Provide the test cases with a `Pinger` instance, where its Worker is mocked.
    """

    # Configure sensor.
    component = load_class("secpi.sensor.pinger", "Pinger")
    parameters = {
        "destination_ip": "localhost",
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
        call.post_log("Pinger: Sensor activated successfully, id=99", 50),
        call.alarm(99, "Hello, world."),
        call.post_log("Pinger: Sensor deactivated successfully, id=99", 50),
    ]

    # Verify log output matches the expectations.
    setup_tuples = [(r.name, r.levelno, r.getMessage()) for r in caplog.get_records(when="setup")]
    assert setup_tuples == [
        ("secpi.util.common", 20, "Loading class successful: secpi.sensor.pinger.Pinger"),
        (
            "secpi.sensor.pinger",
            20,
            "Initializing sensor id=99 with parameters {'destination_ip': 'localhost', 'interval': '0.05', 'max_losses': '0', 'bounce_time': '0'}",
        ),
        ("secpi.sensor.pinger", 10, "Pinger: Sensor initialized"),
    ]

    # This sensor does not send anything to the log by default.
    assert caplog.record_tuples == []

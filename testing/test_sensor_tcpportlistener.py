from unittest.mock import call

import pytest

from tools.sensor import Sensor
from tools.utils import load_class


@pytest.fixture(scope="function")
def tcpportlistener_sensor(worker_mock) -> Sensor:
    """
    Provide the test cases with a `TCPPortListener` instance, where its Worker is mocked.
    """

    # Configure sensor.
    component = load_class("worker.tcpportlistener", "TCPPortListener")
    parameters = {
        "ip": "localhost",
        "port": "54321",
    }

    # Create sensor instance.
    sensor: Sensor = component(id=99, params=parameters, worker=worker_mock)

    yield sensor


def test_sensor_tcpportlistener_alarm(tcpportlistener_sensor, caplog):
    """
    Test the alarm method of the `TCPPortListener`. No sensor logic involved.
    """

    # Invoke alarm, without actually triggering the sensor logic.
    tcpportlistener_sensor.activate()
    tcpportlistener_sensor.alarm("Hello, world.")
    tcpportlistener_sensor.deactivate()

    # Verify the right calls would have been made to the Worker.
    assert tcpportlistener_sensor.worker.mock_calls == [
        call.post_log('TCPPortListener: Sensor activated successfully, id=99', 50),
        call.alarm(99, 'Hello, world.'),
        call.post_log('TCPPortListener: Sensor deactivated successfully, id=99', 50)
    ]

    # Verify log output matches the expectations.
    setup_tuples = [(r.name, r.levelno, r.getMessage()) for r in caplog.get_records(when="setup")]
    assert setup_tuples == [
        ('tools.utils', 20, 'Loading class successful: worker.tcpportlistener.TCPPortListener'),
        ('worker.tcpportlistener', 20, "Initializing sensor id=99 with parameters {'ip': 'localhost', 'port': '54321'}"),
        ('worker.tcpportlistener', 20, "TCPPortListener: Sensor initialized"),
    ]

    # This sensor does not send anything to the log by default.
    assert caplog.record_tuples == [
    ]

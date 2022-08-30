import json
import subprocess
import time
from unittest.mock import call

import pytest

from tools.sensor import Sensor
from tools.utils import load_class


@pytest.fixture(scope="function")
def adam6000_sensor(worker_mock) -> Sensor:
    """
    Provide the test cases with a `AdvantechAdamSensor` instance, where its Worker is mocked.
    """

    # Configure application mock.
    worker_mock.config.update({
        "global": {
            "adam6000": {
                "mqtt_broker_ip": "localhost",
                "mqtt_topic": "Advantech/11E1DAF0ECCE",
                "modbus_seed_enabled": "false",
                "modbus_seed_delay": "0.0",
            },
        }
    })

    # Configure sensor.
    component = load_class("worker.adam6000", "AdvantechAdamSensor")
    parameters = {
        "name": "Ferrata",
        "channel": "di4",
    }

    # Create sensor instance.
    sensor: Sensor = component(id=99, params=parameters, worker=worker_mock)

    yield sensor


def test_sensor_adam6000_alarm(adam6000_sensor, caplog):
    """
    Test the alarm method of the ADAM 6000 sensor. No sensor logic involved.
    """

    # Invoke alarm, without actually triggering the sensor logic.
    adam6000_sensor.activate()
    adam6000_sensor.alarm("Hello, world.")
    adam6000_sensor.deactivate()

    # Verify the right calls would have been made to the Worker.
    assert adam6000_sensor.worker.mock_calls == [
        call.post_log('ADAM: Sensor activated successfully, id=99', 50),
        call.alarm(99, 'Hello, world.'),
        call.post_log('ADAM: Sensor deactivated successfully, id=99', 50)
    ]

    setup_tuples = [(r.name, r.levelno, r.getMessage()) for r in caplog.get_records(when="setup")]
    assert setup_tuples == [
        ('tools.utils', 20, 'Loading class successful: worker.adam6000.AdvantechAdamSensor'),
        ('worker.adam6000', 20, "Initializing sensor id=99 with parameters {'name': 'Ferrata', 'channel': 'di4'}"),
    ]

    assert caplog.record_tuples == [
        ("worker.adam6000", 20, "Starting MQTT subscriber thread"),
        ("worker.adam6000", 20, "Subscribing to MQTT broker at localhost with topic Advantech/11E1DAF0ECCE/data"),
        ("worker.adam6000", 20, "Registering event callback for channel=di4, name=Ferrata"),
        ("worker.adam6000", 20, "Stopping MQTT subscriber thread"),
    ]

    # Verify log output matches the expectations.
    setup_messages = [r.getMessage() for r in caplog.get_records(when="setup")]
    assert "Loading class successful: worker.adam6000.AdvantechAdamSensor" in setup_messages
    assert "Initializing sensor id=99 with parameters {'name': 'Ferrata', 'channel': 'di4'}" in setup_messages
    assert "Starting MQTT subscriber thread" in caplog.messages
    assert "Subscribing to MQTT broker at localhost with topic Advantech/11E1DAF0ECCE/data" in caplog.messages
    assert "Registering event callback for channel=di4, name=Ferrata" in caplog.messages
    assert "Stopping MQTT subscriber thread" in caplog.messages


def test_sensor_adam6000_with_mqtt(adam6000_sensor, caplog):
    """
    Test the sensor logic of the ADAM 6000 sensor by submitting corresponding MQTT messages.
    """

    # Define two device messages, to be delivered using MQTT.
    # They differ on the state value of the ``di4`` channel.
    DEVICE_MESSAGE_1 = json.loads('{"s":1,"t":0,"q":192,"c":1,"di1":true,"di2":true,"di3":true,"di4":true,"di5":false,"di6":false,"di7":false,"di8":true,"di9":true,"di10":true,"di11":true,"di12":true,"do1":true,"do2":true,"do3":false,"do4":false,"do5":false,"do6":false}')
    DEVICE_MESSAGE_2 = json.loads('{"s":1,"t":0,"q":192,"c":1,"di1":true,"di2":true,"di3":true,"di4":false,"di5":false,"di6":false,"di7":false,"di8":true,"di9":true,"di10":true,"di11":true,"di12":true,"do1":true,"do2":true,"do3":false,"do4":false,"do5":false,"do6":false}')

    adam6000_sensor.activate()

    # Invoke sensor by emulating two device messages using MQTT.
    command = f"echo '{json.dumps(DEVICE_MESSAGE_1)}' | mosquitto_pub -h localhost -t 'Advantech/11E1DAF0ECCE/data' -l"
    subprocess.check_output(command, shell=True)
    command = f"echo '{json.dumps(DEVICE_MESSAGE_2)}' | mosquitto_pub -h localhost -t 'Advantech/11E1DAF0ECCE/data' -l"
    subprocess.check_output(command, shell=True)

    # Give system some time for processing.
    time.sleep(0.05)

    adam6000_sensor.deactivate()

    # Verify the right calls would have been made to the Worker.
    assert adam6000_sensor.worker.mock_calls == [
        call.post_log('ADAM: Sensor activated successfully, id=99', 50),
        call.alarm(sensor_id=None, message='Erste Erfassung. Offene Kontakte: Ferrata\n\nSummary message\n\nAlle Kontakte:\n- Kontakt "Ferrata" ist offen\n'),
        call.alarm(99, 'Kontakt Ferrata wurde geschlossen\n\nAlle Kontakte:\n- Kontakt "Ferrata" ist geschlossen\n'),
        call.post_log('ADAM: Sensor deactivated successfully, id=99', 50)
    ]

    # Verify log output matches the expectations.
    setup_messages = [r.getMessage() for r in caplog.get_records(when="setup")]
    assert "Loading class successful: worker.adam6000.AdvantechAdamSensor" in setup_messages
    assert "Initializing sensor id=99 with parameters {'name': 'Ferrata', 'channel': 'di4'}" in setup_messages
    assert "Starting MQTT subscriber thread" in caplog.messages
    assert "Subscribing to MQTT broker at localhost with topic Advantech/11E1DAF0ECCE/data" in caplog.messages
    assert "Registering event callback for channel=di4, name=Ferrata" in caplog.messages
    # assert "ADAM: Sensor activated successfully, id=99" in caplog.messages
    assert """Message: b'{"s": 1, "t": 0,""" in caplog.text
    assert """Data: {'s': 1, 't': 0,""" in caplog.text
    assert "Raising alarm with summary message. Erste Erfassung. Offene Kontakte: Ferrata" in caplog.text
    assert "Sensor state changed. id=99, params={'name': 'Ferrata', 'channel': 'di4'}, channel=di4, value=False" in caplog.messages
    assert "Raising alarm for individual sensor. Kontakt Ferrata wurde geschlossen" in caplog.text
    # assert "ADAM: Sensor deactivated successfully, id=99" in caplog.messages
    assert "Stopping MQTT subscriber thread" in caplog.messages

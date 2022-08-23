"""
About
=====

SecPi sensor adapter for digital input ports of Advantech ADAM-605x devices.
https://www.advantech.com/products/a67f7853-013a-4b50-9b20-01798c56b090/adam-6050/mod_b009c4b4-4b7c-4736-b16f-241978245e6a


Setup
=====
::

    # Install prerequisites.
    pip install paho-mqtt

    # Start RabbitMQ AMQP broker.
    docker run -it --rm --publish=5672:5672 rabbitmq:3.9

    # Start Mosquitto MQTT broker.
    docker run -it --rm --publish=1883:1883 eclipse-mosquitto:2.0.15 mosquitto -c /mosquitto-no-auth.conf


Configuration
=============

Add this snippet to your `worker/config.json`::

    "advantech_adam": {
        "mqtt_broker_ip": "localhost",
        "mqtt_topic": "Advantech/00D0C9EFDBBD/data"
    }


Usage
=====
::

    # Start `AdvantechAdam` example program.
    python -m worker.advantech_adam

    # Submit example MQTT message.
    export PAYLOAD='{"s":1,"t":0,"q":192,"c":1,"di1":true,"di2":true,"di3":true,"di4":true,"di5":false,"di6":false,"di7":false,"di8":true,"di9":true,"di10":true,"di11":true,"di12":true,"do1":true,"do2":true,"do3":false,"do4":false,"do5":false,"do6":false}'
    echo $PAYLOAD | mosquitto_pub -h localhost -t "Advantech/00D0C9EFDBBD/data" -l

"""
import dataclasses
import json
import logging
import sys
import threading
import typing as t

import paho.mqtt.subscribe as subscribe
from tools import config, utils
from tools.sensor import Sensor

logger = logging.getLogger()


class AdvantechAdamConnector:
    """
    Singleton instance for communicating with Advantech ADAM-605x devices using MQTT.
    """

    thread = None

    def __init__(self, mqtt_broker, mqtt_topic):
        self.mqtt_broker = mqtt_broker
        self.mqtt_topic: str = mqtt_topic
        self.registrations: t.Dict[str, "RegistrationItem"] = {}
        self.state: t.Optional[t.Dict] = None

    def start(self):
        """
        Start a single AdvantechAdamCommunicator subscriber thread.
        """
        if AdvantechAdamConnector.thread is None:
            logger.info(f"AdvantechAdam: Starting MQTT subscriber thread")
            AdvantechAdamConnector.thread = threading.Thread(
                name="thr-adam-mqtt-%s" % self.mqtt_broker, target=self.mqtt_subscribe
            )
            AdvantechAdamConnector.thread.start()

    def mqtt_subscribe(self):
        """
        Subscribe to designated broker and topic.
        """
        logger.info(f"Subscribing to MQTT broker at {self.mqtt_broker} with topic {self.mqtt_topic}")
        subscribe.callback(self.on_message, self.mqtt_topic, hostname=self.mqtt_broker)

    def on_message(self, client, userdata, message):
        """
        MQTT message receiver handler.

        The emitted MQTT JSON payload looks like this::
            {
              "s": 1,
              "t": 0,
              "q": 192,
              "c": 1,
              "di1": true,
              "di2": true,
              "di3": true,
              "di4": true,
              "di5": false,
              "di6": false,
              "di7": false,
              "di8": true,
              "di9": true,
              "di10": true,
              "di11": true,
              "di12": true,
              "do1": true,
              "do2": true,
              "do3": false,
              "do4": false,
              "do5": false,
              "do6": false
            }
        """

        # Decode MQTT message.
        logger.debug(f"Message: {message}")
        payload = message.payload.decode("utf-8", "ignore")
        data = json.loads(payload)
        logger.debug(f"Data: {data}")

        # Record states for all registered channels.
        all_responses = []
        for channel, registration_item in self.registrations.items():
            if channel in data:

                response = ResponseItem(
                    channel=channel,
                    value=data[channel],
                    registration=registration_item,
                    alldata=data,
                    mqtt_client=client,
                    mqtt_userdata=userdata,
                )
                if self.state is not None:
                    old_value = self.state.get(channel)
                    response.old_value = old_value
                all_responses.append(response)

        # Dispatch individual channel events, only when state has changed.
        for response in all_responses:
            if self.state is not None:
                if response.old_value != response.value:
                    response.old_value = old_value
                    response.registration.callback(response, all_responses)

        # When component does not have state yet, create single summary message and submit as alarm.
        if self.state is None and all_responses:
            summary_message_long = ResponseItem.summary_humanized("Summary message", all_responses, data)
            summary_message_short = ResponseItem.open_doors_humanized(all_responses)
            alarm_message = f"Erste Erfassung. {summary_message_short}"
            logger.info(f"AdvantechAdam: Raising alarm with summary message. {alarm_message}")
            logger.info(f"AdvantechAdam: Long message:\n{summary_message_long}")
            all_responses[0].registration.sensor.worker.alarm(sensor_id=None, message=alarm_message)

        self.state = data

    def register(self, sensor, callback):
        """
        Register callback event for designated channel.
        """
        channel = sensor.params["channel"]
        name = sensor.params["name"]
        logger.info(f"AdvantechAdam: Registering event callback for channel={channel}, name={name}")
        self.registrations[channel] = RegistrationItem(channel=channel, name=name, sensor=sensor, callback=callback)


class AdvantechAdamSensor(Sensor):
    """
    Wraps individual IO channels on Advantech ADAM-605x devices.
    """

    lock = threading.Lock()
    connector: AdvantechAdamConnector = None

    def __init__(self, id, params, worker):
        logger.info(f"AdvantechAdam: Initializing sensor id={id} with parameters {params}")
        self.stop_thread = False
        super(AdvantechAdamSensor, self).__init__(id, params, worker)

        try:
            self.mqtt_broker_ip = config.get("advantech_adam", {})["mqtt_broker_ip"]
            self.mqtt_topic = config.get("advantech_adam", {})["mqtt_topic"]

        # If config parameters are missing in file.
        except KeyError as ex:
            self.post_err(f"AdvantechAdam: Setup failed, configuration parameter missing: {ex}")
            self.corrupted = True
            return

    def activate(self):
        if not self.corrupted:
            self.start_mqtt_subscriber()

            def event_handler(response: ResponseItem, all_responses: t.List["ResponseItem"]):
                logger.debug(
                    f"Sensor state changed. id={self.id}, params={self.params}, channel={response.registration.channel}, value={response.value}"
                )
                message_title = response.door_transition_humanized()
                message = ResponseItem.summary_humanized(message_title, all_responses, response.alldata)

                logger.info(f"AdvantechAdam: Raising alarm for individual sensor. {message}")
                self.alarm(message)
                if self.stop_thread:
                    response.mqtt_client.disconnect()

            AdvantechAdamSensor.connector.register(self, event_handler)

            self.post_log(f"AdvantechAdam: Sensor activated successfully, id={self.id}", utils.LEVEL_INFO)
        else:
            self.post_err(f"AdvantechAdam: Sensor could not be activated, id={self.id}")

    def deactivate(self):
        if not self.corrupted:
            self.stop_thread = True
            logger.info(f"TODO: Stop MQTT subscriber thread")
        else:
            self.post_err("AdvantechAdam: Sensor could not be deactivated")

    def start_mqtt_subscriber(self):
        """
        Start a single MQTT subscriber thread.
        """
        with AdvantechAdamSensor.lock:
            if AdvantechAdamSensor.connector is None:
                AdvantechAdamSensor.connector = AdvantechAdamConnector(self.mqtt_broker_ip, self.mqtt_topic)
                AdvantechAdamSensor.connector.start()


@dataclasses.dataclass
class RegistrationItem:
    """
    Hold information about a registered channel.

    It signals the machinery that we are interested about state changes on this channel.
    """

    channel: str
    name: str
    sensor: Sensor = None
    callback: t.Callable = None


@dataclasses.dataclass
class ResponseItem:
    """
    When a state change on a specific channel occurs, the downstream machinery receives this object.

    It can be used to create an appropriate notification message.
    """

    channel: str
    value: t.Optional[t.Union[int, bool]] = None
    old_value: t.Optional[t.Union[int, bool]] = None
    registration: t.Optional[RegistrationItem] = None
    alldata: t.Optional[t.Dict] = None
    mqtt_client: t.Optional = None
    mqtt_userdata: t.Optional[t.Dict] = None

    @staticmethod
    def summary_humanized(title: str, items: t.List["ResponseItem"], all_data):
        summary_message = ""
        for state in items:
            summary_message += f'- {state.door_state_humanized()}\n'

        summary_message = f"{title}\n\nAlle Türen:\n{summary_message}\nAlle Daten:\n{all_data}"
        return summary_message

    @staticmethod
    def open_doors_humanized(items: t.List["ResponseItem"]):
        open_doors = []
        for state in items:
            sensor_id = state.registration.sensor.id
            sensor_channel = state.registration.channel
            sensor_name = state.registration.name
            value = state.value
            if value is True:
                open_doors.append(sensor_name)
        return f"Offene Türen: {', '.join(open_doors) or 'keine'}"

    def door_state_humanized(self):
        sensor_name = self.registration.name
        sensor_value = self.value
        if sensor_value is True:
            verb = "offen"
        elif sensor_value is False:
            verb = "geschlossen"
        else:
            verb = "unbekannt"
        return f'Tür "{sensor_name}" ist {verb}'

    def door_transition_humanized(self):
        sensor_name = self.registration.name
        sensor_value = self.value
        if sensor_value is True:
            verb = "geöffnet"
        elif sensor_value is False:
            verb = "geschlossen"
        else:
            verb = "kaputtgemacht"
        return f"Tür {sensor_name} wurde {verb}"


if __name__ == "__main__":
    """
    Example program to create worker context, add some sensors, and invoke the machinery.
    """

    # Initialize a worker context.
    sys.argv = ["worker.py", "."]
    from worker.worker import Worker

    Worker.CONVERSATION_DELAY = 0
    worker = Worker()
    worker.active = True

    # Create multiple sensor instances and activate them.
    adam1 = AdvantechAdamSensor(914, {"channel": "di4", "name": "Ferrata"}, worker)
    adam2 = AdvantechAdamSensor(917, {"channel": "di7", "name": "Acquedotto"}, worker)
    adam1.activate()
    adam2.activate()

    logger.info("Worker launched successfully")

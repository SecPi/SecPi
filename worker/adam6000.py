"""
About
=====

SecPi sensor adapter for digital input ports of Advantech ADAM-605x devices.

- https://www.advantech.com/products/a67f7853-013a-4b50-9b20-01798c56b090/adam-6050/mod_b009c4b4-4b7c-4736-b16f-241978245e6a
- https://advdownload.advantech.com/productfile/Downloadfile5/1-24AIR0Z/ADAM-6000_User_Manaul_Ed.11_FINAL.pdf
- https://advdownload.advantech.com/productfile/Downloadfile4/1-1EGDNCJ/ADAM%20MQTT%20manual%20V1.pdf
- http://support.elmark.com.pl/advantech/pdf/iag/ADAM_MQTT-manual.pdf
- https://www.mouser.com/catalog/additional/Advantech_ADAM_6000_User_Manaul_Ed_10_FINAL.pdf
- https://www.integral-system.fr/shop/media/product/file/adam6200_user_manual_ed_4-5f6b0ebe7c493.pdf


Setup
=====
::

    # Install prerequisites, using `apt`.
    apt install python3-stopit python3-paho-mqtt python3-pymodbus python3-click python3-prompt-toolkit
    pip install func-timeout

    # Alternatively, install prerequisites using `pip`.
    pip install paho-mqtt pymodbus[repl] func-timeout

    # Start RabbitMQ AMQP broker.
    docker run -it --rm --publish=5672:5672 rabbitmq:3.9

    # Start Mosquitto MQTT broker.
    docker run -it --rm --publish=1883:1883 eclipse-mosquitto:2.0.15 mosquitto -c /mosquitto-no-auth.conf


Configuration
=============

Add this snippet to your `manager/config.json`::

    "global": {
            "adam6000": {
                    "mqtt_broker_ip": "localhost",
                    "mqtt_topic": "Advantech/00D0C9EFDBBD"
            }
    }


Usage
=====
::

    # Start `AdvantechAdam` example program.
    python -m worker.adam6000

    # Submit example MQTT message.
    export PAYLOAD1='{"s":1,"t":0,"q":192,"c":1,"di1":true,"di2":true,"di3":true,"di4":true,"di5":false,"di6":false,"di7":false,"di8":true,"di9":true,"di10":true,"di11":true,"di12":true,"do1":true,"do2":true,"do3":false,"do4":false,"do5":false,"do6":false}'
    export PAYLOAD2='{"s":1,"t":0,"q":192,"c":1,"di1":true,"di2":true,"di3":true,"di4":false,"di5":false,"di6":false,"di7":false,"di8":true,"di9":true,"di10":true,"di11":true,"di12":true,"do1":true,"do2":true,"do3":false,"do4":false,"do5":false,"do6":false}'
    echo $PAYLOAD1 | mosquitto_pub -h localhost -t "Advantech/00D0C9EFDBBD/data" -l
    echo $PAYLOAD2 | mosquitto_pub -h localhost -t "Advantech/00D0C9EFDBBD/data" -l


HTTP interface
==============
::

    curl "http://192.168.178.10/digitalinput/all/value" --user "root:00000000"
    <?xml version="1.0" ?><ADAM-6050 status="OK"><DI><ID>0</ID><VALUE>1</VALUE></DI><DI><ID>1</ID><VALUE>1</VALUE></DI><DI><ID>2</ID><VALUE>0</VALUE></DI><DI><ID>3</ID><VALUE>1</VALUE></DI><DI><ID>4</ID><VALUE>0</VALUE></DI><DI><ID>5</ID><VALUE>0</VALUE></DI><DI><ID>6</ID><VALUE>0</VALUE></DI><DI><ID>7</ID><VALUE>1</VALUE></DI><DI><ID>8</ID><VALUE>0</VALUE></DI><DI><ID>9</ID><VALUE>0</VALUE></DI><DI><ID>10</ID><VALUE>0</VALUE></DI><DI><ID>11</ID><VALUE>0</VALUE></DI></ADAM-6050>

Modbus interface
================
::

    python -m pymodbus.repl.main tcp --host 192.168.178.10
    client.read_discrete_inputs address 1 count 12

    {
        "bits": [
            true,
            false,
            true,
            false,
            false,
            false,
            true,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false,
            false
        ]
    }


Documentation
=============

Module Ethernet Protocol and Port (ADAM-6200 User Manual, p. 57)::

    TCP Modbus          TCP 502
    Download            TCP 5450
    Config. Upload      TCP 5452
    Web Server          TCP 80
    Search Engine       UDP 5048
    ASCII CMD           UDP 1025
    P2P/GCL             UDP 1025 Configurable
    Data Stream         UDP 5168
    GCL remote Message  UDP 5168

ADAM MQTT Manual, p. 8::

    What: Set publishing data streaming
    CMD: %aaSETMQTTSTxxxxxxxx
    CMD: %01SETMQTTST00001000

    interval time
    aa:         always 01
    xxxxxxxx:   publishing data streaming interval time in millisecond
                (0032~FFFFFFFF)

    Return: >01
    Error:  ?01

"""
import collections
import dataclasses
import json
import logging
import sys
import threading
import time
import typing as t

import func_timeout
import pymodbus
from paho.mqtt import subscribe
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from tools import config, utils
from tools.sensor import Sensor

logger = logging.getLogger()


class AdvantechAdamModbusConnector:
    def __init__(
        self,
        device_hostname: t.Optional[str] = None,
        mqtt_broker: t.Optional[str] = None,
        mqtt_topic: t.Optional[str] = None,
    ):
        self.device_hostname: str = device_hostname
        self.mqtt_broker: str = mqtt_broker
        self.mqtt_topic: str = mqtt_topic

        if self.device_hostname is None:
            timeout = 2.0
            logger.info("Hostname not set, resolving per MQTT")
            try:
                func_timeout.func_timeout(timeout, self.resolve_hostname)
            except func_timeout.exceptions.FunctionTimedOut:
                logger.info(f"Resolving hostname per MQTT failed, timed out after {timeout} seconds")

        if self.device_hostname is None:
            raise ValueError(f"Unable to discover hostname of Advantech ADAM device")

    def resolve_hostname(self):
        """
        Retrieve IP address from retained MQTT message.

        mosquitto_sub -t '#' -v
        {"status":"disconnect","name":"ADAM6050","macid":"00D0C9EFDBBD","ipaddr":"192.168.178.10"}
        """
        topic = f"{self.mqtt_topic}/Device_Status"
        logger.info(f"Reading IP address from MQTT topic {topic} at broker {self.mqtt_broker}")
        response = subscribe.simple(topic, hostname=self.mqtt_broker)
        device_status = json.loads(response.payload)
        self.device_hostname = device_status["ipaddr"]

    def read_input_ports(self):
        """
        Request state of digital input ports using Modbus.
        """
        hostname = self.device_hostname
        logger.info(f"Connecting to device at {hostname} using Modbus")
        try:
            client = ModbusClient(hostname)
            input_data = self.modbus_read_inputs(client)
            client.close()
        except pymodbus.exceptions.ConnectionException:
            logger.exception(f"Unable to connect to device at {hostname} using Modbus")
            return

        data = collections.OrderedDict()
        for i in range(12):
            channel = "di" + str(i + 1)
            state = input_data[i]
            data[channel] = bool(state)

        return data

    @staticmethod
    def modbus_read_inputs(client, address=0, count=12):
        """
        Read state about digital input ports via Modbus.
        """
        rr = client.read_discrete_inputs(address=address, count=count, slave=0x01)
        assert not rr.isError()
        return rr.bits[:count]


class AdvantechAdamMqttConnector:
    """
    Singleton instance for communicating with Advantech ADAM-605x devices using MQTT.
    """

    thread = None

    def __init__(self, mqtt_broker, mqtt_topic):
        self.mqtt_broker: str = mqtt_broker
        self.mqtt_topic: str = mqtt_topic
        self.registrations: t.Dict[str, "RegistrationItem"] = {}
        self.state: t.Optional[t.Dict] = None

    def start(self):
        """
        Start a single AdvantechAdamCommunicator subscriber thread.
        """

        # First of all, attempt to request the initial state from the device.
        # However, delay it for some seconds to give the application some time to register
        # all sensors. Otherwise, there will be no chance to generate and submit a summary
        # notification message.
        def seed_later():
            time.sleep(3)
            self.seed_state()

        threading.Thread(target=seed_later).start()

        # Then, start the MQTT subscriber thread singleton.
        if AdvantechAdamMqttConnector.thread is None:
            logger.info(f"ADAM: Starting MQTT subscriber thread")
            AdvantechAdamMqttConnector.thread = threading.Thread(
                name="thr-adam-mqtt-%s" % self.mqtt_broker, target=self.mqtt_subscribe
            )
            AdvantechAdamMqttConnector.thread.start()

    def seed_state(self):
        """
        Send request using Modbus in order to receive the initial state.
        """
        logger.info("Seeding state by requesting port status from device using Modbus")
        try:
            aamc = AdvantechAdamModbusConnector(mqtt_broker=self.mqtt_broker, mqtt_topic=self.mqtt_topic)
            self.state = aamc.read_input_ports()
            logger.info(f"Received initial state: {self.state}")

            # Create single summary message and submit as alarm.
            all_responses = self.process_device_data(data=self.state)
            self.submit_summary_alarm(all_responses, self.state)

        except:
            logger.exception("Seeding state failed")

    def mqtt_subscribe(self):
        """
        Subscribe to designated broker and topic.
        """
        topic = f"{self.mqtt_topic}/data"
        logger.info(f"Subscribing to MQTT broker at {self.mqtt_broker} with topic {topic}")
        subscribe.callback(self.on_message, topic, hostname=self.mqtt_broker)

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
        all_responses = self.process_device_data(
            data=data, more_data={"mqtt_client": client, "mqtt_userdata": userdata}
        )

        # Dispatch individual channel events, only when state has changed.
        for response in all_responses:
            if self.state is not None:
                if response.old_value != response.value:
                    response.registration.callback(response, all_responses)

        # When component does not have state yet, create single summary message and submit as alarm.
        if self.state is None and all_responses:
            self.submit_summary_alarm(all_responses, data)

        self.state = data

    def register(self, sensor, callback):
        """
        Register callback event for designated channel.
        """
        channel = sensor.params["channel"]
        name = sensor.params["name"]
        logger.info(f"ADAM: Registering event callback for channel={channel}, name={name}")
        self.registrations[channel] = RegistrationItem(channel=channel, name=name, sensor=sensor, callback=callback)

    def unregister(self, sensor):
        """
        Unregister callback event for designated channel.
        """
        channel = sensor.params["channel"]
        if channel in self.registrations:
            del self.registrations[channel]

    def process_device_data(self, data: t.Dict, more_data: t.Optional[t.Dict] = None) -> t.List["ResponseItem"]:
        """
        Match registered channels against port status response from device and create response model.
        """
        more_data = more_data or {}
        all_responses = []
        for channel, registration_item in self.registrations.items():
            if channel in data:

                response = ResponseItem(
                    channel=channel,
                    value=data[channel],
                    registration=registration_item,
                    alldata=data,
                )
                response.__dict__.update(**more_data)

                if self.state is not None:
                    old_value = self.state.get(channel)
                    response.old_value = old_value

                all_responses.append(response)

        return all_responses

    def submit_summary_alarm(self, all_responses: t.List["ResponseItem"], data: t.Dict):
        """
        Build and submit a summary alarm, informing about the total state of all ports.
        """
        summary_message_long = ResponseItem.summary_humanized("Summary message", all_responses, data)
        summary_message_short = ResponseItem.open_circuit_humanized(all_responses)
        alarm_message = f"Erste Erfassung. {summary_message_short}\n\n{summary_message_long}"
        logger.info(f"ADAM: Raising alarm with summary message. {alarm_message}")
        # logger.info(f"ADAM: Long message:\n{summary_message_long}")
        all_responses[0].registration.sensor.worker.alarm(sensor_id=None, message=alarm_message)


class AdvantechAdamSensor(Sensor):
    """
    Wraps individual IO channels on Advantech ADAM-605x devices.
    """

    lock = threading.Lock()
    connector: AdvantechAdamMqttConnector = None

    def __init__(self, id, params, worker):
        logger.info(f"ADAM: Initializing sensor id={id} with parameters {params}")
        super(AdvantechAdamSensor, self).__init__(id, params, worker)

        try:
            settings = config.get("global", {})["adam6000"]
            self.mqtt_broker_ip = settings["mqtt_broker_ip"]
            self.mqtt_topic = settings["mqtt_topic"]

        # If config parameters are missing in file.
        except KeyError as ex:
            self.post_err(f"ADAM: Setup failed, configuration parameter missing: {ex}")
            self.corrupted = True
            return

    def activate(self):
        if not self.corrupted:
            self.start_mqtt_subscriber()

            def event_handler(response: ResponseItem, all_responses: t.List["ResponseItem"]):
                logger.debug(
                    f"Sensor state changed. id={self.id}, params={self.params}, channel={response.registration.channel}, value={response.value}"
                )
                message_title = response.circuit_transition_humanized()
                message = ResponseItem.summary_humanized(message_title, all_responses, response.alldata)

                logger.info(f"ADAM: Raising alarm for individual sensor. {message}")
                self.alarm(message)

            AdvantechAdamSensor.connector.register(self, event_handler)

            self.post_log(f"ADAM: Sensor activated successfully, id={self.id}", utils.LEVEL_INFO)
        else:
            self.post_err(f"ADAM: Sensor could not be activated, id={self.id}")

    def deactivate(self):
        if not self.corrupted:
            AdvantechAdamSensor.connector.unregister(self)
            self.post_log(f"ADAM: Sensor deactivated successfully, id={self.id}", utils.LEVEL_INFO)
        else:
            self.post_err(f"ADAM: Sensor could not be deactivated, id={self.id}")

    def start_mqtt_subscriber(self):
        """
        Start a single MQTT subscriber thread.
        """
        with AdvantechAdamSensor.lock:
            if AdvantechAdamSensor.connector is None:
                AdvantechAdamSensor.connector = AdvantechAdamMqttConnector(self.mqtt_broker_ip, self.mqtt_topic)
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
            summary_message += f"- {state.circuit_state_humanized()}\n"

        # summary_message = f"{title}\n\nAlle Kontakte:\n{summary_message}\nAlle Daten:\n{all_data}"
        summary_message = f"{title}\n\nAlle Kontakte:\n{summary_message}"
        return summary_message

    @staticmethod
    def open_circuit_humanized(items: t.List["ResponseItem"]):
        open_circuit = []
        for state in items:
            sensor_id = state.registration.sensor.id
            sensor_channel = state.registration.channel
            sensor_name = state.registration.name
            value = state.value
            if value is True:
                open_circuit.append(sensor_name)
        return f"Offene Kontakte: {', '.join(open_circuit) or 'keine'}"

    def circuit_state_humanized(self):
        sensor_name = self.registration.name
        sensor_value = self.value
        if sensor_value is True:
            verb = "offen"
        elif sensor_value is False:
            verb = "geschlossen"
        else:
            verb = "kaputt"
        return f'Kontakt "{sensor_name}" ist {verb}'

    def circuit_transition_humanized(self):
        sensor_name = self.registration.name
        sensor_value = self.value
        if sensor_value is True:
            verb = "geöffnet"
        elif sensor_value is False:
            verb = "geschlossen"
        else:
            verb = "kaputtgemacht"
        return f"Kontakt {sensor_name} wurde {verb}"


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

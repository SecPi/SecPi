import datetime
import json
import logging
import os
import shutil
import sys
import threading
import uuid

import pika

from secpi.model import constants
from secpi.util.common import (
    check_late_arrival,
    get_ip_addresses,
    load_class,
    setup_logging,
)
from secpi.util.config import ApplicationConfig
from tools.amqp import AMQPAdapter
from tools.base import Service
from tools.cli import StartupOptions, parse_cmd_args

logger = logging.getLogger(__name__)


class Worker(Service):

    CONVERSATION_DELAY = 4.2

    def __init__(self, config: ApplicationConfig):
        self.config = config
        self.actions = []
        self.sensors = []
        self.active = False

        # TODO: Make paths configurable.
        self.data_directory = "/var/tmp/secpi/worker_data"
        self.zip_directory = "/var/tmp/secpi"

        logger.info("Initializing worker")

        self.prepare_data_directory()

        # Connect to messaging bus.
        self.bus = AMQPAdapter(
            hostname=config.get("rabbitmq", {}).get("master_ip", "localhost"),
            port=int(config.get("rabbitmq", {}).get("master_port", 5672)),
            username=config.get("rabbitmq", {}).get("user"),
            password=config.get("rabbitmq", {}).get("password"),
            buffer_undelivered=True,
        )
        self.connect()

        # if we don't have a pi id we need to request the initial config, afterwards we have to reconnect
        # to the queues which are specific to the pi id -> hence, call connect again
        if not config.get("pi_id"):
            logger.info("No Pi ID found, will request initial configuration from manager")
            self.fetch_init_config()
        else:
            logger.info("Setting up sensors and actions")
            self.active = config.get("active")
            self.setup_sensors()
            self.setup_actions()
            logger.info("Setup of sensors and actions completed")

    def connect(self):

        self.bus.connect()
        channel: "pika.channel.Channel" = self.bus.channel

        # Declare exchanges and queues.
        channel.exchange_declare(exchange=constants.EXCHANGE, exchange_type="direct")

        # INIT CONFIG MODE
        # When the worker does not have an identifier, only define a basic
        # setup to receive an initial configuration from the manager.
        if not self.config.get("pi_id"):
            result = channel.queue_declare(queue="init-callback", exclusive=True)
            self.callback_queue = result.method.queue
            channel.queue_bind(queue=self.callback_queue, exchange=constants.EXCHANGE)
            channel.queue_declare(queue=constants.QUEUE_INIT_CONFIG)
            channel.basic_consume(queue=self.callback_queue, on_message_callback=self.got_init_config, auto_ack=True)

        # OPERATIVE MODE
        # When the worker has an assigned identifier, it is assumed it already has
        # received a valid configuration. In this case, connect all the queues and
        # callbacks.
        else:
            # Get worker identifier from configuration.
            worker_identifier = str(self.config.get("pi_id"))

            # Declare all the queues.
            channel.queue_declare(queue=constants.QUEUE_OPERATIONAL + worker_identifier)
            channel.queue_declare(queue=constants.QUEUE_ACTION + worker_identifier)
            channel.queue_declare(queue=constants.QUEUE_CONFIG + worker_identifier)
            channel.queue_declare(queue=constants.QUEUE_DATA)
            channel.queue_declare(queue=constants.QUEUE_ALARM)
            channel.queue_declare(queue=constants.QUEUE_LOG)

            # Specify the queues we want to listen to, including the callback.
            channel.basic_consume(
                queue=constants.QUEUE_OPERATIONAL + worker_identifier,
                on_message_callback=self.got_operational,
                auto_ack=True,
            )
            channel.basic_consume(
                queue=constants.QUEUE_ACTION + worker_identifier, on_message_callback=self.got_action, auto_ack=True
            )
            channel.basic_consume(
                queue=constants.QUEUE_CONFIG + worker_identifier, on_message_callback=self.got_config, auto_ack=True
            )

    def start(self):
        self.bus.subscribe_forever(on_error=self.on_bus_error)

    def on_bus_error(self):
        logger.info("Trying to reconnect to AMQP broker")
        self.bus.disconnect()
        self.connect()

        # Process undelivered messages.
        # TODO: Could invoking `process_message_queue` make problems if the manager replies too fast?
        self.bus.process_undelivered_messages(delay=self.CONVERSATION_DELAY)

    # sends a message to the manager
    def send_msg(self, rk, body, **kwargs):
        self.bus.publish(exchange=constants.EXCHANGE, routing_key=rk, body=body, **kwargs)
        return True

    # sends a message to the manager
    def send_json_msg(self, rk, body, **kwargs):
        properties = pika.BasicProperties(content_type="application/json")
        self.bus.publish(
            exchange=constants.EXCHANGE, routing_key=rk, body=json.dumps(body), properties=properties, **kwargs
        )
        return True

    def post_err(self, msg):
        logger.error(msg)
        err = {
            "msg": msg,
            "level": constants.LEVEL_ERR,
            "sender": f"Worker {self.config.get('pi_id')}",
            "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.send_json_msg(constants.QUEUE_LOG, err)

    def post_log(self, msg, lvl):
        logger.info(msg)
        lg = {
            "msg": msg,
            "level": lvl,
            "sender": f"Worker {self.config.get('pi_id')}",
            "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.send_json_msg(constants.QUEUE_LOG, lg)

    def load_plugin(self, module_name, class_name):
        """
        Load plugin module.
        """
        module_candidates = [f"worker.{module_name}", module_name]
        error_message = f"Failed to import class {class_name} from modules '{module_candidates}'"
        component = load_class(module_candidates, class_name, errors="ignore")
        if component is None:
            self.post_err(error_message)
        return component

    def fetch_init_config(self):
        """
        AMQP: Request initial configuration from Manager.
        """
        ip_addresses = get_ip_addresses()
        if ip_addresses:
            self.corr_id = str(uuid.uuid4())
            logger.info("Sending initial configuration request to manager")
            properties = pika.BasicProperties(
                reply_to=self.callback_queue, correlation_id=self.corr_id, content_type="application/json"
            )
            self.send_msg(constants.QUEUE_INIT_CONFIG, json.dumps(ip_addresses), properties=properties)
        else:
            logger.error("Wasn't able to find any IP address(es), please check your network configuration. Exiting.")
            quit()

    def got_init_config(self, ch, method, properties, body):
        """
        AMQP: Receive initial configuration from Manager.
        """

        if len(body) == 0:
            logger.warning("Received empty configuration, will skip processing")

            # After a while, ask for configuration again.
            self.bus.sleep(self.CONVERSATION_DELAY)
            self.fetch_init_config()
            return

        logger.info("Received initial config %r" % (body))
        if self.corr_id == properties.correlation_id:  # we got the right config
            try:
                new_conf = json.loads(body)
                new_conf["rabbitmq"] = self.config.get("rabbitmq")
            except Exception as e:
                logger.exception("Wasn't able to read JSON config from manager:\n%s" % e)

                # After a while, ask for configuration again.
                self.bus.sleep(self.CONVERSATION_DELAY)
                self.fetch_init_config()
                return

            logger.info("Trying to apply config and reconnect")
            self.apply_config(new_conf)
            self.connection_cleanup()
            self.connect()  # hope this is the right spot
            logger.info("Initial config activated")
            self.start()
        else:
            logger.info("This config isn't meant for us")

    # Create a zip of all the files which were collected while actions were executed
    def prepare_data(self):
        try:
            if os.listdir(self.data_directory):  # check if there are any files available
                shutil.make_archive(
                    "%s/%s" % (self.zip_directory, self.config.get("pi_id")), "zip", self.data_directory
                )
                logger.info("Created ZIP file")
                return True
            else:
                logger.info("No data to zip")
                return False
        except OSError as oe:
            self.post_err(
                "Pi with id '%s' wasn't able to prepare data for manager:\n%s" % (self.config.get("pi_id"), oe)
            )
            logger.error("Wasn't able to prepare data for manager: %s" % oe)

    # Remove all the data that was created during the alarm, unlink == remove
    def cleanup_data(self):
        try:
            os.unlink("%s/%s.zip" % (self.zip_directory, self.config.get("pi_id")))
            for the_file in os.listdir(self.data_directory):
                file_path = os.path.join(self.data_directory, the_file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            logger.info("Cleaned up files")
        except OSError as oe:
            self.post_err("Pi with id '%s' wasn't able to execute cleanup:\n%s" % (self.config.get("pi_id"), oe))
            logger.error("Wasn't able to clean up data directory: %s" % oe)

    # callback method which processes the actions which originate from the manager
    def got_action(self, ch, method, properties, body):
        if self.active:
            msg = json.loads(body)
            late_arrival = check_late_arrival(datetime.datetime.strptime(msg["datetime"], "%Y-%m-%d %H:%M:%S"))

            if late_arrival:
                logger.info("Received old action from manager:%s" % body)
                return  # we don't have to send a message to the data queue since the timeout will be over anyway

            # http://stackoverflow.com/questions/15085348/what-is-the-use-of-join-in-python-threading
            logger.info("Received action from manager:%s" % body)
            threads = []

            for act in self.actions:
                t = threading.Thread(name="thread-%s" % (act.id), target=act.execute)
                threads.append(t)
                t.start()

            # wait for threads to finish
            for t in threads:
                t.join()

            if self.prepare_data():  # check if there is any data to send
                with open("%s/%s.zip" % (self.zip_directory, self.config.get("pi_id")), "rb") as zip_file:
                    byte_stream = zip_file.read()
                self.send_msg(constants.QUEUE_DATA, byte_stream)
                logger.info("Sent data to manager")
                self.cleanup_data()
            else:
                logger.info("No data to send")
                # Send empty message which acts like a finished
                self.send_msg(constants.QUEUE_DATA, "")
        else:
            logger.debug("Received action but wasn't active")

    def apply_config(self, new_config):
        # check if new config changed
        if new_config != self.config.asdict():
            # disable while loading config
            self.active = False

            # TODO: deactivate queues
            logger.info("Cleaning up actions and sensors")
            self.cleanup_sensors()
            self.cleanup_actions()

            # TODO: check valid config file?!
            # write config to file
            try:
                self.config.update(new_config)
                self.config.save()
            except Exception:
                logger.exception(f"Writing configuration file failed")

            if self.config.get("active"):
                logger.info("Activating actions and sensors")
                self.setup_sensors()
                self.setup_actions()
                # TODO: activate queues
                self.active = True

            logger.info("Config saved successfully")
        else:
            logger.info("Config didn't change")

    def got_config(self, ch, method, properties, body):
        logger.info("Received config %r" % (body))

        try:
            new_conf = json.loads(body)
        except Exception:
            logger.exception("Reading JSON config from manager failed")
            return

        # we don't get the rabbitmq config sent to us, so add the current one
        new_conf["rabbitmq"] = self.config.get("rabbitmq")

        self.apply_config(new_conf)

    # Initialize all the sensors for operation and add callback method
    # TODO: check for duplicated sensors
    def setup_sensors(self):
        if not self.config.get("sensors"):
            logger.info("No sensors configured")
            return
        for sensor in self.config.get("sensors"):
            try:
                logger.info("Registering sensor: %s" % sensor["id"])
                s = self.load_plugin(sensor["module"], sensor["class"])
                sen = s(sensor["id"], sensor["params"], self)
                sen.activate()
            except Exception as e:
                self.post_err(
                    "Pi with id '%s' wasn't able to register sensor '%s':\n%s"
                    % (self.config.get("pi_id"), sensor["class"], e)
                )
            else:
                self.sensors.append(sen)
                logger.info(f"Registered sensor {sensor}")

    def cleanup_sensors(self):
        # remove the callbacks
        if self.sensors:
            for sensor in self.sensors:
                sensor.deactivate()
                logger.debug("Removed sensor: %d" % int(sensor.id))

        self.sensors = []

    # Initialize all the actions
    def setup_actions(self):
        if not self.config.get("actions"):
            logger.info("No actions configured")
            return
        for action in self.config.get("actions"):
            try:
                logger.info("Trying to register action: %s" % action["id"])
                a = self.load_plugin(action["module"], action["class"])
                act = a(action["id"], action["params"], self)
            except Exception as e:  # AttributeError, KeyError
                self.post_err(
                    "Pi with id '%s' wasn't able to register action '%s':\n%s"
                    % (self.config.get("pi_id"), action["class"], e)
                )
            else:
                self.actions.append(act)
                logger.info(f"Registered action {action}")

    def cleanup_actions(self):
        for a in self.actions:
            a.cleanup()

        self.actions = []

    # callback for the sensors, sends a message with info to the manager
    def alarm(self, sensor_id, message):
        if self.active:
            logger.info("Sensor with id %s detected something" % sensor_id)

            msg = {
                "pi_id": self.config.get("pi_id"),
                "sensor_id": sensor_id,
                "message": message,
                "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # send a message to the alarmQ and tell which sensor signaled
            self.send_json_msg(constants.QUEUE_ALARM, msg)

        else:
            logger.warning("Not submitting alarm because worker is not active")

    def prepare_data_directory(self):
        logger.info(f"SecPi data directory is {self.data_directory}")
        try:
            os.makedirs(self.data_directory, exist_ok=True)
        except OSError as ex:
            self.post_err("Pi with id '%s' failed creating data directory: %s" % (self.config.get("pi_id"), ex))

    def connection_cleanup(self):
        self.bus.disconnect()


def run_worker(options: StartupOptions):

    try:
        app_config = ApplicationConfig(filepath=options.app_config)
        app_config.load()
    except:
        logger.exception("Loading configuration failed")
        sys.exit(1)

    w = None
    try:
        w = Worker(config=app_config)
        w.start()
    except KeyboardInterrupt:
        logger.info("Shutting down worker")
        if w:
            w.cleanup_actions()
            w.cleanup_sensors()

        # Help a bit to completely terminate the AMQP connection.
        # TODO: Probably the root cause for this is elsewhere. Investigate.
        sys.exit(130)


def main():
    options = parse_cmd_args()
    setup_logging(level=logging.DEBUG, config_file=options.logging_config, log_file=options.log_file)
    run_worker(options)
    logging.shutdown()


if __name__ == "__main__":
    main()

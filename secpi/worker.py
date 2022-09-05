import datetime
import json
import logging
import sys
import typing as t
import uuid

import pika

from secpi.model import constants
from secpi.model.action import Action, ActionResponse
from secpi.model.message import ActionRequestMessage, AlarmMessage
from secpi.model.sensor import Sensor
from secpi.model.service import Service
from secpi.model.settings import StartupOptions
from secpi.util.amqp import AMQPAdapter
from secpi.util.cli import parse_cmd_args
from secpi.util.common import (
    check_late_arrival,
    get_ip_addresses,
    get_random_identifier,
    load_class,
    run_tasks,
    setup_logging,
)
from secpi.util.config import ApplicationConfig

logger = logging.getLogger(__name__)


class Worker(Service):

    # TODO: Make those values configurable.
    CONVERSATION_DELAY = 4.2
    ACTION_TIMEOUT = 60.0

    def __init__(self, config: ApplicationConfig):
        super().__init__()
        self.config = config
        self.actions: t.List[Action] = []
        self.sensors: t.List[Sensor] = []
        self.active = False

        self.worker_id = self.config.get("worker").get("worker_id")

        logger.info(f"Initializing worker {self.worker_id}")

        # Queue for initial configuration request.
        # The name of the exclusive callback queue used for requesting the initial configuration.
        self.callback_queue: str = None

        # Random correlation identifier for initial configuration request.
        # Used to make sure to only process the actually requested configuration.
        self.corr_id: str = None

        # Connect to messaging bus.
        self.bus = AMQPAdapter.from_uri(config.get("amqp", {}).get("uri"))
        self.connect()

        # if we don't have a worker id we need to request the initial config, afterwards we have to reconnect
        # to the queues which are specific to the worker id -> hence, call connect again
        if not self.worker_id:
            self.fetch_init_config()
        else:
            logger.info("Setting up sensors and actions")
            self.active = self.config.get("worker").get("active")
            self.setup_sensors()
            self.setup_actions()
            logger.info("Setup of sensors and actions completed")

        logger.info("Worker is ready")

    def connect(self):

        self.bus.connect()
        channel: "pika.channel.Channel" = self.bus.channel

        # Declare exchanges and queues.
        channel.exchange_declare(exchange=constants.EXCHANGE, exchange_type="direct")

        # INIT CONFIG MODE
        # When the worker does not have an identifier, only define a basic
        # setup to receive an initial configuration from the manager.
        if not self.worker_id:
            logger.info("Worker is in INIT CONFIG mode")
            callback_queue_id = get_random_identifier(length=6)
            self.callback_queue = f"init-callback-{callback_queue_id}"
            channel.queue_declare(queue=self.callback_queue)
            channel.queue_bind(queue=self.callback_queue, exchange=constants.EXCHANGE)
            channel.queue_declare(queue=constants.QUEUE_INIT_CONFIG)
            channel.basic_consume(queue=self.callback_queue, on_message_callback=self.got_init_config, auto_ack=True)

        # OPERATIVE MODE
        # When the worker has an assigned identifier, it is assumed it already has
        # received a valid configuration. In this case, connect all the queues and
        # callbacks.
        else:
            logger.info("Worker is in OPERATIVE mode")
            # Get worker identifier from configuration.
            worker_identifier = str(self.worker_id)

            # Declare exchanges and queues.
            channel.exchange_declare(exchange=constants.EXCHANGE, exchange_type="direct")

            # Declare all the queues.
            channel.queue_declare(queue=constants.QUEUE_OPERATIONAL + worker_identifier)
            channel.queue_declare(queue=constants.QUEUE_ACTION + worker_identifier)
            channel.queue_declare(queue=constants.QUEUE_CONFIG + worker_identifier)
            channel.queue_declare(queue=constants.QUEUE_ACTION_RESPONSE)
            channel.queue_declare(queue=constants.QUEUE_ALARM)
            channel.queue_declare(queue=constants.QUEUE_LOG)

            channel.queue_bind(queue=constants.QUEUE_OPERATIONAL + worker_identifier, exchange=constants.EXCHANGE)
            channel.queue_bind(queue=constants.QUEUE_ACTION + worker_identifier, exchange=constants.EXCHANGE)
            channel.queue_bind(queue=constants.QUEUE_CONFIG + worker_identifier, exchange=constants.EXCHANGE)
            channel.queue_bind(queue=constants.QUEUE_ACTION_RESPONSE, exchange=constants.EXCHANGE)
            channel.queue_bind(queue=constants.QUEUE_ALARM, exchange=constants.EXCHANGE)
            channel.queue_bind(queue=constants.QUEUE_LOG, exchange=constants.EXCHANGE)

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

    def stop(self):
        self.cleanup_actions()
        self.cleanup_sensors()
        super().stop()

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
            "sender": f"Worker {self.worker_id}",
            "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.send_json_msg(constants.QUEUE_LOG, err)

    def post_log(self, msg, lvl):
        logger.info(msg)
        lg = {
            "msg": msg,
            "level": lvl,
            "sender": f"Worker {self.worker_id}",
            "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.send_json_msg(constants.QUEUE_LOG, lg)

    def load_plugin(self, module_name, class_name):
        """
        Load plugin module.
        """
        # TODO: Think about this when the Worker intends to load other plugins than only Sensors or Actions.
        module_candidates = [f"secpi.sensor.{module_name}", f"secpi.action.{module_name}", module_name]
        error_message = f"Failed to import class {class_name} from modules '{module_candidates}'"
        component = load_class(module_candidates, class_name, errors="ignore")
        if component is None:
            self.post_err(error_message)
        return component

    def fetch_init_config(self):
        """
        AMQP: Request initial configuration from Manager.
        """
        logger.info("Requesting initial configuration from Manager")
        ip_addresses = get_ip_addresses()
        if ip_addresses:
            if self.callback_queue is None:
                logger.warning("Unable to send initial configuration request, because there is no callback queue")

            self.corr_id = str(uuid.uuid4())
            logger.info(f"Sending initial configuration request to manager with id={self.corr_id}")
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
            logger.warning(f"The configuration request response with id={self.corr_id} isn't meant for us")

    def got_action(self, ch, method, properties, body):
        """
        When the worker receives a signal to run an action.
        """
        if self.active:

            logger.debug(f"Received action: {body}")

            action_message = ActionRequestMessage.from_json(body)
            late_arrival = check_late_arrival(action_message.datetime)

            # Do not execute late actions.
            if late_arrival:
                logger.info("Received late action, not executing: %s" % body)
                return

            # Run all actions and ...
            tasks = [action.execute for action in self.actions]
            futures = run_tasks(tasks)

            # ... wait for them to finish within `action_timeout` seconds.
            results: t.List[ActionResponse] = [future.result(timeout=self.ACTION_TIMEOUT) for future in futures]

            # Create Zip archive from action task results.
            zip_filelist, zip_payload = ActionResponse.make_zip(results)

            if zip_filelist:
                logger.info(f"Created ZIP file with {len(zip_filelist)} items")
                self.send_msg(constants.QUEUE_ACTION_RESPONSE, zip_payload)
                logger.info("Sent data to manager")
            else:
                logger.info("No data to send")
                # Send `NODATA` message.
                self.send_msg(constants.QUEUE_ACTION_RESPONSE, "__NODATA__")

        else:
            logger.debug("Received action but wasn't active")

    def apply_config(self, new_config):
        """
        Apply received configuration locally.
        """

        # We don't get the `amqp` config snippet sent to us, so add the current one.
        # TODO: Only whitelist specific keys, like `sensors` and `actions`.
        new_config["amqp"] = self.config.get("amqp")
        new_config["directories"] = self.config.get("directories", {})

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
                logger.info("Config saved successfully")
            except Exception:
                logger.exception("Writing configuration file failed")

            if self.config.get("worker").get("active"):
                logger.info("Activating actions and sensors")
                self.setup_sensors()
                self.setup_actions()
                # TODO: activate queues
                self.active = True

        else:
            logger.info("Config didn't change")

    def got_config(self, ch, method, properties, body):
        logger.info("Received config %r" % (body))

        if self.config.get("worker").get("config_no_update"):
            logger.info("Configuration is tagged with `config_no_update`, skip updating")
            return

        try:
            new_conf = json.loads(body)
        except Exception:
            logger.exception("Reading JSON config from manager failed")
            return

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
            except Exception as ex:
                self.post_err(
                    f"Worker with id '{self.worker_id}' wasn't able to register sensor '{sensor['class']}': {ex}"
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
            if not action.get("active_state"):
                continue
            try:
                logger.info("Registering action: %s" % action["id"])
                a = self.load_plugin(action["module"], action["class"])
                act = a(action["id"], action["params"], self)
            except Exception as ex:
                self.post_err(
                    f"Worker with id '{self.worker_id}' wasn't able to register sensor '{action['class']}': {ex}"
                )
            else:
                self.actions.append(act)
                logger.info(f"Registered action: {action}")

    def cleanup_actions(self):
        for action in self.actions:
            action.cleanup()
            logger.debug("Removed action: %d" % int(action.id))

        self.actions = []

    # callback for the sensors, sends a message with info to the manager
    def alarm(self, sensor_id, message):
        if self.active:
            logger.info("Sensor with id %s detected something" % sensor_id)

            # Send message to the alarm queue.
            msg = AlarmMessage(
                worker_id=self.worker_id,
                sensor_id=sensor_id,
                message=message,
                datetime=datetime.datetime.now(),
            )
            self.send_json_msg(constants.QUEUE_ALARM, msg.to_dict())

        else:
            logger.warning("Not submitting alarm because worker is not active")

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


def main(options: t.Optional[StartupOptions] = None):
    if not options:
        options = parse_cmd_args()
    setup_logging(level=logging.DEBUG, config_file=options.logging_config, log_file=options.log_file)
    run_worker(options)
    logging.shutdown()


if __name__ == "__main__":
    main()

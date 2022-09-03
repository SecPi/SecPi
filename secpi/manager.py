import datetime
import hashlib
import json
import logging
import os
import pathlib
import sys
import tempfile
import threading
import time
import typing as t

import appdirs
import pika

from secpi.model import constants
from secpi.model.dbmodel import (
    Action,
    Alarm,
    LogEntry,
    Notifier,
    Sensor,
    Setup,
    Worker,
    Zone,
)
from secpi.model.message import ActionRequestMessage, AlarmMessage, NotificationMessage
from secpi.model.service import Service
from secpi.model.settings import StartupOptions
from secpi.util.amqp import AMQPAdapter
from secpi.util.cli import parse_cmd_args
from secpi.util.common import load_class, setup_logging, str_to_value
from secpi.util.config import ApplicationConfig
from secpi.util.database import DatabaseAdapter

logger = logging.getLogger(__name__)


class Manager(Service):
    def __init__(self, config: ApplicationConfig):
        super().__init__()
        self.config = config
        self.notifiers = []

        self.database_uri = config.get("database", {}).get("uri")
        self.data_timeout = int(config.get("data_timeout", 180))
        self.holddown_timer = int(config.get("holddown_timer", 210))

        # Configure "alarms" directory.
        self.alarm_dir = config.get("directories", {}).get("alarms", str(self.alarms_directory))
        logger.info(f"Storing alarms to {self.alarm_dir}")

        logger.info("Initializing manager")
        self.standalone_mode = False

        self.holddown_state = False
        self.num_of_workers = 0
        self.received_data_counter = 0

        # Connect to database.
        self.db = DatabaseAdapter(uri=self.database_uri)
        try:
            self.db.connect()
        except:
            logger.exception(f"Connecting to database at '{self.database_uri}' failed")
            sys.exit(1)

        # Connect to messaging bus.
        self.bus = AMQPAdapter.from_config(config)
        self.connect()

        # Check if any setup is active.
        setups = self.db.session.query(Setup).all()
        activate_notifiers = False
        for setup in setups:
            if setup.active_state:
                activate_notifiers = True
            logger.info(f"Found active setup: {setup.name}")
            break

        # When a setup is active, also activate the notifiers.
        if activate_notifiers:
            self.setup_notifiers()
            self.num_of_workers = (
                self.db.session.query(Worker)
                .join((Action, Worker.actions))
                .filter(Worker.active_state == True)
                .filter(Action.active_state == True)
                .count()
            )

        logger.info("Manager is ready")

    def connect(self):

        self.bus.connect()
        channel: "pika.channel.Channel" = self.bus.channel

        # Declare exchanges and queues.
        channel.exchange_declare(exchange=constants.EXCHANGE, exchange_type="direct")

        # Define queues: data, alarm and action & config for every pi.
        channel.queue_declare(queue=constants.QUEUE_OPERATIONAL + "m")
        channel.queue_declare(queue=constants.QUEUE_ACTION_RESPONSE)
        channel.queue_declare(queue=constants.QUEUE_ALARM)
        channel.queue_declare(queue=constants.QUEUE_ON_OFF)
        channel.queue_declare(queue=constants.QUEUE_LOG)
        channel.queue_declare(queue=constants.QUEUE_INIT_CONFIG)
        channel.queue_bind(queue=constants.QUEUE_ON_OFF, exchange=constants.EXCHANGE)
        channel.queue_bind(queue=constants.QUEUE_ACTION_RESPONSE, exchange=constants.EXCHANGE)
        channel.queue_bind(queue=constants.QUEUE_ALARM, exchange=constants.EXCHANGE)
        channel.queue_bind(queue=constants.QUEUE_LOG, exchange=constants.EXCHANGE)
        channel.queue_bind(queue=constants.QUEUE_INIT_CONFIG, exchange=constants.EXCHANGE)

        # Load workers from database.
        workers = self.db.session.query(Worker).all()
        for pi in workers:
            channel.queue_declare(queue=constants.QUEUE_ACTION + str(pi.id))
            channel.queue_declare(queue=constants.QUEUE_CONFIG + str(pi.id))
            channel.queue_bind(queue=constants.QUEUE_ACTION + str(pi.id), exchange=constants.EXCHANGE)
            channel.queue_bind(queue=constants.QUEUE_CONFIG + str(pi.id), exchange=constants.EXCHANGE)

        # Define callbacks for alarm and data queues.
        channel.basic_consume(
            queue=constants.QUEUE_OPERATIONAL + "m", on_message_callback=self.got_operational, auto_ack=True
        )
        channel.basic_consume(queue=constants.QUEUE_ALARM, on_message_callback=self.got_alarm, auto_ack=True)
        channel.basic_consume(queue=constants.QUEUE_ON_OFF, on_message_callback=self.got_on_off, auto_ack=True)
        channel.basic_consume(
            queue=constants.QUEUE_ACTION_RESPONSE, on_message_callback=self.got_action_response, auto_ack=True
        )
        channel.basic_consume(queue=constants.QUEUE_LOG, on_message_callback=self.got_log, auto_ack=True)
        channel.basic_consume(
            queue=constants.QUEUE_INIT_CONFIG, on_message_callback=self.got_config_request, auto_ack=True
        )

    def start(self):
        self.bus.subscribe_forever(on_error=self.on_bus_error)

    def on_bus_error(self):
        logger.info("Trying to reconnect to AMQP broker")
        self.bus.disconnect()
        self.connect()

    def load_plugin(self, module_name, class_name):
        """
        Load plugin module.
        """
        # TODO: Think about this when the manager intends to load other plugins than only Notifiers.
        module_candidates = [f"secpi.notifier.{module_name}", module_name]
        component = load_class(module_candidates, class_name, errors="ignore")
        if component is None:
            self.log_err(f"Unable to import class {class_name} from modules '{module_candidates}'")
        return component

    # this method is used to send messages to a queue
    def send_message(self, rk, body, **kwargs):
        try:
            self.bus.publish(exchange=constants.EXCHANGE, routing_key=rk, body=body, **kwargs)
            logger.info("Sending data to queue %s" % rk)
            return True
        except Exception as e:
            logger.exception("Error while sending data to queue: %s" % e)
            return False

    # this method is used to send json messages to a queue
    def send_json_message(self, rk, body, **kwargs):
        try:
            properties = pika.BasicProperties(content_type="application/json")
            logger.info("Sending json data to queue %s" % rk)
            self.bus.publish(
                exchange=constants.EXCHANGE, routing_key=rk, body=json.dumps(body), properties=properties, **kwargs
            )
            return True
        except Exception as e:
            logger.exception("Error while sending json data to queue: %s" % e)
            return False

    # helper method to create error log entry
    def log_err(self, msg):
        logger.error(msg)
        log_entry = LogEntry(level=constants.LEVEL_ERR, message=str(msg), sender="Manager")
        self.db.session.add(log_entry)
        self.db.session.commit()

    # helper method to create error log entry
    def log_msg(self, msg, level):
        if level == constants.LEVEL_DEBUG:
            logger.debug(msg)
        elif level == constants.LEVEL_INFO:
            logger.info(msg)
        elif level == constants.LEVEL_WARN:
            logger.warning(msg)
        elif level == constants.LEVEL_ERR:
            logger.error(msg)
        log_entry = LogEntry(level=level, message=str(msg), sender="Manager")
        self.db.session.add(log_entry)
        self.db.session.commit()

    def got_config_request(self, ch, method, properties, body):
        ip_addresses = json.loads(body)
        logger.info("Got config request with following IP addresses: %s" % ip_addresses)

        pi_id = None
        worker = self.db.session.query(Worker).filter(Worker.address.in_(ip_addresses)).first()
        if worker:
            pi_id = worker.id
            logger.debug("Found worker id %s for IP address %s" % (pi_id, worker.address))
        else:
            logger.error("Unable able to find worker for given IP address(es)")
            reply_properties = pika.BasicProperties(correlation_id=properties.correlation_id)
            self.bus.publish(
                exchange=constants.EXCHANGE, properties=reply_properties, routing_key=properties.reply_to, body=""
            )
            return

        config = self.prepare_config(pi_id)
        logger.info("Sending initial config to worker with id %s" % pi_id)
        reply_properties = pika.BasicProperties(
            correlation_id=properties.correlation_id, content_type="application/json"
        )
        self.bus.publish(
            exchange=constants.EXCHANGE,
            properties=reply_properties,
            routing_key=properties.reply_to,
            body=json.dumps(config),
        )

    def got_action_response(self, ch, method, properties, body):
        """
        When the manager receives data from a worker after executing an action.
        """
        logger.info("Received response from action invocation")
        newFile_bytes = bytearray(body)
        if newFile_bytes:  # only write data when body is not empty
            filename = hashlib.md5(newFile_bytes).hexdigest() + ".zip"
            # TODO: Revisit and review.
            # AttributeError: 'Manager' object has no attribute 'current_alarm_dir'
            filepath = os.path.join(self.current_alarm_dir, filename)
            try:
                logger.info(f"Writing data to current alarm dir: {filepath}")
                with open(filepath, "wb") as newFile:
                    newFile.write(newFile_bytes)
            except Exception:
                logger.exception("Failed to write data to current alarm dir")
        self.received_data_counter += 1

    # callback for log messages
    def got_log(self, ch, method, properties, body):
        log = json.loads(body)
        logger.debug("Got log message from %s: %s" % (log["sender"], log["msg"]))
        log_entry = LogEntry(
            level=log["level"],
            message=str(log["msg"]),
            sender=log["sender"],
            logtime=str_to_value(log["datetime"]),
        )
        self.db.session.add(log_entry)
        self.db.session.commit()

    # callback for when a setup gets activated/deactivated
    def got_on_off(self, ch, method, properties, body):
        msg = json.loads(body)

        self.cleanup_notifiers()

        if msg["active_state"] == True:
            self.setup_notifiers()
            logger.info("Activating setup: %s" % msg["setup_name"])

        workers = self.db.session.query(Worker).filter(Worker.active_state == True).all()
        for pi in workers:
            config = self.prepare_config(pi.id)
            # check if we are deactivating --> worker should be deactivated!
            if msg["active_state"] == False:
                config["active"] = False
                logger.info("Deactivating setup: %s" % msg["setup_name"])

            self.send_json_message(constants.QUEUE_CONFIG + str(pi.id), config)
            logger.info("Sent config to worker %s" % pi.name)

    def got_alarm(self, ch, method, properties, body):
        """
        When a worker raises an alarm.
        """

        alarm = AlarmMessage.from_json(body)

        if not alarm.late_arrival:
            logger.info("Received alarm: %s" % body)
        else:
            logger.info("Received late alarm: %s" % body)

        alarm_log_level = constants.LEVEL_WARN
        if self.holddown_state:
            alarm.holddown = True
            alarm_log_level = constants.LEVEL_INFO

        # Store alarm item into database.
        self.store_alarm(alarm)

        # Create `NotificationMessage` object.
        # Enrich alarm message by human-readable worker- and sensor-names, retrieved from the database.
        worker = self.db.session.query(Worker).filter(Worker.id == alarm.worker_id).first()
        sensor = self.db.session.query(Sensor).filter(Sensor.id == alarm.sensor_id).first()
        notification = NotificationMessage(
            sensor_name=sensor.name if sensor else f"id={alarm.sensor_id}",
            worker_name=worker.name if worker else f"id={alarm.worker_id}",
            alarm=alarm,
        )

        # Submit alarm item to log output.
        self.log_msg(
            f"{notification.alarm.get_label()}"
            f"Alarm from sensor {notification.sensor_name}, worker {notification.worker_name}: "
            f"{notification.alarm.message}",
            alarm_log_level,
        )

        # TODO: Manage holddown per sensor.
        if not self.holddown_state:

            # Enable holddown for the subsequent alarms.
            holddown_thread = threading.Thread(name="thread-holddown", target=self.holddown)
            holddown_thread.start()

            # Create alarm directory.
            # TODO: Revisit and review.
            # AttributeError: 'Manager' object has no attribute 'current_alarm_dir'
            self.current_alarm_dir = os.path.join(self.alarm_dir, time.strftime("%Y%m%d_%H%M%S"))
            try:
                os.makedirs(self.current_alarm_dir)
                logger.debug(f"Created directory for alarm: {self.current_alarm_dir}")
            except OSError:
                logger.exception(f"Creating directory for alarm failed: {self.current_alarm_dir}")
            self.received_data_counter = 0

            # Execute actions on workers.
            self.execute_actions(alarm)

            # Actually send notifications.
            self.send_notification(notification)

    def execute_actions(self, alarm: AlarmMessage):
        """
        Invoke actions on all Workers.
        """
        logger.info("Executing actions")

        # iterate over workers and send "execute"
        workers = (
            self.db.session.query(Worker)
            .join((Action, Worker.actions))
            .filter(Worker.active_state == True)
            .filter(Action.active_state == True)
            .all()
        )
        self.num_of_workers = len(workers)

        action_message = ActionRequestMessage(
            msg="execute",
            datetime=datetime.datetime.now(),
            # Forward full alarm information into the action message.
            # This makes it possible to be more flexible within all downstream components.
            alarm=alarm,
        )

        # TODO: When in standalone mode, make sure NoBroker spawns dedicated threads here.
        action_message_json = action_message.to_dict()
        for worker in workers:
            self.send_json_message(constants.QUEUE_ACTION + str(worker.id), action_message_json)

    def store_alarm(self, alarm: AlarmMessage):
        """
        Store alarm into database.
        """
        alarm = Alarm(sensor_id=alarm.sensor_id, message=alarm.render_message())
        self.db.session.add(alarm)
        self.db.session.commit()

    def send_notification(self, notification: NotificationMessage):
        """
        Invoke all configured notifiers.
        """

        # Start timeout thread for workers to reply.
        timeout_thread = threading.Thread(
            name="thread-timeout", target=self.notify, kwargs={"notification": notification}
        )
        timeout_thread.start()

    # initialize the notifiers
    def setup_notifiers(self):
        logger.info("Setting up notifiers")
        notifiers = self.db.session.query(Notifier).filter(Notifier.active_state == True).all()

        for notifier in notifiers:
            params = {}
            for p in notifier.params:
                params[p.key] = p.value

            n = self.load_plugin(notifier.module, notifier.cl)
            noti = n(notifier.id, params)
            self.notifiers.append(noti)
            logger.info("Set up notifier %s" % notifier.cl)

    # timeout thread which sends the received data from workers
    def notify(self, notification: NotificationMessage):

        for i in range(0, self.data_timeout):
            if self.received_data_counter < self.num_of_workers:  # not all data here yet
                logger.debug(
                    "Waiting for data from workers: data counter: %d, #workers: %d"
                    % (self.received_data_counter, self.num_of_workers)
                )
                time.sleep(1)
            else:
                logger.debug("Received all data from workers, cancelling the timeout")
                break
        # continue code execution
        if self.received_data_counter < self.num_of_workers:
            self.log_msg(
                "TIMEOUT: Only %d out of %d workers replied with data"
                % (self.received_data_counter, self.num_of_workers),
                constants.LEVEL_INFO,
            )

        # let the notifiers do their work
        notification_message = notification.to_dict()

        # Translate dictionary to satisfy notifiers.
        # TODO: Pass notification object directly, without needing to serialize as dictionary.
        notification_message["sensor"] = notification_message["sensor_name"]
        notification_message["worker"] = notification_message["worker_name"]
        notification_message["message"] = notification.alarm.render_message()
        for notifier in self.notifiers:
            try:
                notifier.notify(notification_message)
            except Exception as e:
                logger.exception("Notification failed")
                self.log_err("Error notifying %u: %s" % (notifier.id, e))

    # go into holddown state, while in this state subsequent alarms are interpreted as one alarm
    def holddown(self):

        # Skip holddown in testing mode.
        if "PYTEST_CURRENT_TEST" in os.environ:
            return

        self.holddown_state = True
        for i in range(0, self.holddown_timer):
            time.sleep(1)
        logger.debug("Holddown is over")
        self.holddown_state = False

    # cleanup the notifiers
    def cleanup_notifiers(self):
        for n in self.notifiers:
            n.cleanup()

        self.notifiers = []

    def prepare_config(self, pi_id):
        logger.info("Preparing config for worker with id %s" % pi_id)
        conf = {
            "pi_id": pi_id,
            "active": False,  # default to false, will be overriden if should be true
        }

        sensors = (
            self.db.session.query(Sensor)
            .join(Zone)
            .join((Setup, Zone.setups))
            .filter(Setup.active_state == True)
            .filter(Sensor.worker_id == pi_id)
            .all()
        )

        # if we have sensors we are active
        if len(sensors) > 0:
            conf["active"] = True

        # A configuration setting container which will be available on all workers.
        conf["global"] = self.config.get("global")

        conf_sensors = []
        for sen in sensors:
            para = {}
            # create params array
            for p in sen.params:
                para[p.key] = p.value

            conf_sen = {"id": sen.id, "name": sen.name, "module": sen.module, "class": sen.cl, "params": para}
            conf_sensors.append(conf_sen)

        conf["sensors"] = conf_sensors

        actions: t.List[Action] = (
            self.db.session.query(Action)
            .join((Worker, Action.workers))
            .filter(Worker.id == pi_id)
            .filter(Action.active_state == True)
            .all()
        )

        # if we have actions we are also active
        if len(actions) > 0:
            conf["active"] = True

        conf_actions = []
        # iterate over all actions
        for act in actions:
            para = {}
            # create params array
            for p in act.params:
                para[p.key] = p.value

            conf_act = {"id": act.id, "module": act.module, "class": act.cl, "params": para}
            conf_actions.append(conf_act)

        conf["actions"] = conf_actions

        logger.info(f"Generated config: {conf}")
        return conf

    @property
    def alarms_directory(self):
        data_directory = os.path.join(appdirs.user_data_dir("secpi"))
        if "PYTEST_CURRENT_TEST" in os.environ:
            data_directory = tempfile.mkdtemp()
        path = pathlib.Path(data_directory).joinpath("alarms")
        path.mkdir(parents=True, exist_ok=True)
        return path


def run_manager(options: StartupOptions):

    try:
        app_config = ApplicationConfig(filepath=options.app_config)
        app_config.load()
    except:
        logger.exception("Loading configuration failed")
        sys.exit(1)

    mg = None
    try:
        mg = Manager(config=app_config)
        mg.start()
    except KeyboardInterrupt:
        logger.info("Shutting down manager")
        if mg:
            mg.cleanup_notifiers()


def main(options: t.Optional[StartupOptions] = None):
    if not options:
        options = parse_cmd_args()
    setup_logging(level=logging.DEBUG, config_file=options.logging_config, log_file=options.log_file)
    run_manager(options)
    logging.shutdown()


if __name__ == "__main__":
    main()

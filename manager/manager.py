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

import appdirs
import pika
from tools import utils
from tools.amqp import AMQPAdapter
from tools.base import Service
from tools.cli import StartupOptions, parse_cmd_args
from tools.config import ApplicationConfig
from tools.db.database import DatabaseAdapter
from tools.db.objects import Action, Alarm, LogEntry, Sensor, Setup, Worker, Zone, Notifier
from tools.utils import load_class, setup_logging

logger = logging.getLogger(__name__)


class Manager(Service):

	def __init__(self, config: ApplicationConfig):
		self.config = config
		self.notifiers = []

		self.database_uri = config.get("database", {}).get("uri")
		self.data_timeout = int(config.get("data_timeout", 180))
		self.holddown_timer = int(config.get("holddown_timer", 210))

		# Configure "alarms" directory.
		self.alarm_dir = config.get("directories", {}).get("alarms", str(self.alarms_directory))
		logger.info(f"Storing alarms to {self.alarm_dir}")

		logger.info("Initializing manager")

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
		self.bus = AMQPAdapter(
			hostname=config.get('rabbitmq', {}).get('master_ip', 'localhost'),
			port=int(config.get('rabbitmq', {}).get('master_port', 5672)),
			username=config.get('rabbitmq')['user'],
			password=config.get('rabbitmq')['password'],
		)
		self.connect()

		# Debug output about setups and state.
		setups = self.db.session.query(Setup).all()
		activate_notifiers = False
		for setup in setups:
			logger.debug("name: %s active:%s" % (setup.name, setup.active_state))
			if setup.active_state:
				activate_notifiers = True

		if activate_notifiers:
			self.setup_notifiers()
			self.num_of_workers = self.db.session.query(Worker).join((Action, Worker.actions)).filter(Worker.active_state == True).filter(Action.active_state == True).count()

		logger.info("Manager is ready")

	def connect(self):

		self.bus.connect()
		channel: "pika.channel.Channel" = self.bus.channel

		# Declare exchanges and queues.
		channel.exchange_declare(exchange=utils.EXCHANGE, exchange_type='direct')

		# Define queues: data, alarm and action & config for every pi.
		channel.queue_declare(queue=utils.QUEUE_OPERATIONAL + "m")
		channel.queue_declare(queue=utils.QUEUE_DATA)
		channel.queue_declare(queue=utils.QUEUE_ALARM)
		channel.queue_declare(queue=utils.QUEUE_ON_OFF)
		channel.queue_declare(queue=utils.QUEUE_LOG)
		channel.queue_declare(queue=utils.QUEUE_INIT_CONFIG)
		channel.queue_bind(exchange=utils.EXCHANGE, queue=utils.QUEUE_ON_OFF)
		channel.queue_bind(exchange=utils.EXCHANGE, queue=utils.QUEUE_DATA)
		channel.queue_bind(exchange=utils.EXCHANGE, queue=utils.QUEUE_ALARM)
		channel.queue_bind(exchange=utils.EXCHANGE, queue=utils.QUEUE_LOG)
		channel.queue_bind(exchange=utils.EXCHANGE, queue=utils.QUEUE_INIT_CONFIG)
		
		# Load workers from database.
		workers = self.db.session.query(Worker).all()
		for pi in workers:
			channel.queue_declare(queue=utils.QUEUE_ACTION+str(pi.id))
			channel.queue_declare(queue=utils.QUEUE_CONFIG+str(pi.id))
			channel.queue_bind(exchange=utils.EXCHANGE, queue=utils.QUEUE_ACTION+str(pi.id))
			channel.queue_bind(exchange=utils.EXCHANGE, queue=utils.QUEUE_CONFIG+str(pi.id))

		# Define callbacks for alarm and data queues.
		channel.basic_consume(self.got_operational, queue=utils.QUEUE_OPERATIONAL + "m", no_ack=True)
		channel.basic_consume(self.got_alarm, queue=utils.QUEUE_ALARM, no_ack=True)
		channel.basic_consume(self.got_on_off, queue=utils.QUEUE_ON_OFF, no_ack=True)
		channel.basic_consume(self.got_data, queue=utils.QUEUE_DATA, no_ack=True)
		channel.basic_consume(self.got_log, queue=utils.QUEUE_LOG, no_ack=True)
		channel.basic_consume(self.got_config_request, queue=utils.QUEUE_INIT_CONFIG, no_ack=True)

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
		module_candidates = [f"manager.{module_name}", module_name]
		component = load_class(module_candidates, class_name, errors="ignore")
		if component is None:
			self.log_err(f"Unable to import class {class_name} from modules '{module_candidates}'")
		return component

	# this method is used to send messages to a queue
	def send_message(self, rk, body, **kwargs):
		try:
			self.bus.publish(exchange=utils.EXCHANGE, routing_key=rk, body=body, **kwargs)
			logger.info("Sending data to %s" % rk)
			return True
		except Exception as e:
			logger.exception("Error while sending data to queue:\n%s" % e)
			return False
	
	# this method is used to send json messages to a queue
	def send_json_message(self, rk, body, **kwargs):
		try:
			properties = pika.BasicProperties(content_type='application/json')
			self.bus.publish(exchange=utils.EXCHANGE, routing_key=rk, body=json.dumps(body), properties=properties, **kwargs)
			logger.info("Sending json data to %s" % rk)
			return True
		except Exception as e:
			logger.exception("Error while sending json data to queue")
			return False
	
	# helper method to create error log entry
	def log_err(self, msg):
		logger.error(msg)
		log_entry = LogEntry(level=utils.LEVEL_ERR, message=str(msg), sender="Manager")
		self.db.session.add(log_entry)
		self.db.session.commit()
	
	# helper method to create error log entry
	def log_msg(self, msg, level):
		logger.info(msg)
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
			self.bus.publish(exchange=utils.EXCHANGE, properties=reply_properties, routing_key=properties.reply_to, body="")
			return
		
		config = self.prepare_config(pi_id)
		logger.info("Sending initial config to worker with id %s" % pi_id)
		reply_properties = pika.BasicProperties(correlation_id=properties.correlation_id, content_type='application/json')
		self.bus.publish(exchange=utils.EXCHANGE, properties=reply_properties, routing_key=properties.reply_to, body=json.dumps(config))

	# callback method for when the manager recieves data after a worker executed its actions
	def got_data(self, ch, method, properties, body):
		logger.info("Got data")
		newFile_bytes = bytearray(body)
		if newFile_bytes: #only write data when body is not empty
			filename = hashlib.md5(newFile_bytes).hexdigest() + ".zip"
			filepath = os.path.join(self.current_alarm_dir, filename)
			try:
				with open(filepath, "wb") as newFile:
					newFile.write(newFile_bytes)
					logger.info("Data written")
			except IOError as ie: # File can't be written, e.g. permissions wrong, directory doesn't exist
				logger.exception("Wasn't able to write received data: %s" % ie)
		self.received_data_counter += 1

	# callback for log messages
	def got_log(self, ch, method, properties, body):
		log = json.loads(body)
		logger.debug("Got log message from %s: %s"%(log['sender'], log['msg']))
		log_entry = LogEntry(level=log['level'], message=str(log['msg']), sender=log['sender'], logtime=utils.str_to_value(log['datetime']))
		self.db.session.add(log_entry)
		self.db.session.commit()

	# callback for when a setup gets activated/deactivated
	def got_on_off(self, ch, method, properties, body):
		msg = json.loads(body)
		
		self.cleanup_notifiers()
		
		if(msg['active_state'] == True):
			self.setup_notifiers()
			logger.info("Activating setup: %s" % msg['setup_name'])
		
		
		workers = self.db.session.query(Worker).filter(Worker.active_state == True).all()
		for pi in workers:
			config = self.prepare_config(pi.id)
			# check if we are deactivating --> worker should be deactivated!
			if(msg['active_state'] == False):
				config["active"] = False
				logger.info("Deactivating setup: %s" % msg['setup_name'])
				
			self.send_json_message(utils.QUEUE_CONFIG+str(pi.id), config)
			logger.info("Sent config to worker %s"%pi.name)

	# callback method which gets called when a worker raises an alarm
	def got_alarm(self, ch, method, properties, body):
		msg = json.loads(body)
		late_arrival = utils.check_late_arrival(datetime.datetime.strptime(msg["datetime"], "%Y-%m-%d %H:%M:%S"))

		if not late_arrival:
			logger.info("Received alarm: %s"%body)
		else:
			logger.info("Received old alarm: %s"%body)

		if not self.holddown_state:
			# put into holddown
			holddown_thread = threading.Thread(name="thread-holddown", target=self.holddown)
			holddown_thread.start()

			self.current_alarm_dir = os.path.join(self.alarm_dir, time.strftime("%Y%m%d_%H%M%S"))
			try:
				os.makedirs(self.current_alarm_dir)
				logger.debug(f"Created directory for alarm: {self.current_alarm_dir}")
			except OSError:
				logger.exception(f"Creating directory for alarm failed: {self.current_alarm_dir}")
			self.received_data_counter = 0

			# iterate over workers and send "execute"
			workers = self.db.session.query(Worker).join((Action, Worker.actions)).filter(Worker.active_state == True).filter(Action.active_state == True).all()
			self.num_of_workers = len(workers)
			action_message = { "msg": "execute",
								"datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
								"late_arrival":late_arrival}
			for pi in workers:
				self.send_json_message(utils.QUEUE_ACTION+str(pi.id), action_message)
			
			worker = self.db.session.query(Worker).filter(Worker.id == msg['pi_id']).first()
			sensor = self.db.session.query(Sensor).filter(Sensor.id == msg['sensor_id']).first()
			
			# create log entry for db
			if not late_arrival:
				al = Alarm(sensor_id=msg['sensor_id'], message=msg['message'])
				self.log_msg("New alarm from %s on sensor %s: %s"%( (worker.name if worker else msg['pi_id']) , (sensor.name if sensor else msg['sensor_id']) , msg['message']), utils.LEVEL_WARN)
			else:
				al = Alarm(sensor_id=msg['sensor_id'], message="Late Alarm: %s" %msg['message'])
				self.log_msg("Old alarm from %s on sensor %s: %s"%( (worker.name if worker else msg['pi_id']) , (sensor.name if sensor else msg['sensor_id']) , msg['message']), utils.LEVEL_WARN)
			
			self.db.session.add(al)
			self.db.session.commit()
			
			# TODO: add information about late arrival of alarm
			notif_info = {
				"message": msg['message'],
				"sensor": (sensor.name if sensor else msg['sensor_id']),
				"sensor_id": msg['sensor_id'],
				"worker": (worker.name if worker else msg['pi_id']),
				"worker_id": msg['pi_id']
			}

			# start timeout thread for workers to reply
			timeout_thread = threading.Thread(name="thread-timeout", target=self.notify, args=[notif_info])
			timeout_thread.start()
		else: # --> holddown state
			self.log_msg("Alarm during holddown state from %s on sensor %s: %s"%(msg['pi_id'], msg['sensor_id'], msg['message']), utils.LEVEL_INFO)
			al = Alarm(sensor_id=msg['sensor_id'], message="Alarm during holddown state: %s" % msg['message'])
			self.db.session.add(al)
			self.db.session.commit()

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
	def notify(self, info):
		for i in range(0, self.data_timeout):
			if self.received_data_counter < self.num_of_workers: #not all data here yet
				logger.debug("Waiting for data from workers: data counter: %d, #workers: %d" % (self.received_data_counter, self.num_of_workers))
				time.sleep(1)
			else:
				logger.debug("Received all data from workers, cancelling the timeout")
				break
		# continue code execution
		if self.received_data_counter < self.num_of_workers:
			self.log_msg("TIMEOUT: Only %d out of %d workers replied with data"%(self.received_data_counter, self.num_of_workers), utils.LEVEL_INFO)
		
		# let the notifiers do their work
		for notifier in self.notifiers:
			try:
				notifier.notify(info)
			except Exception as e:
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
			"active": False, # default to false, will be overriden if should be true
		}
		
		sensors = self.db.session.query(Sensor).join(Zone).join((Setup, Zone.setups)).filter(Setup.active_state == True).filter(Sensor.worker_id == pi_id).all()
		
		# if we have sensors we are active
		if(len(sensors)>0):
			conf['active'] = True
		
		# A configuration setting container which will be available on all workers.
		conf['global'] = self.config.get('global')

		conf_sensors = []
		for sen in sensors:
			para = {}
			# create params array
			for p in sen.params:
				para[p.key] = p.value
			
			conf_sen = {
				"id": sen.id,
				"name": sen.name,
				"module": sen.module,
				"class": sen.cl,
				"params": para
			}
			conf_sensors.append(conf_sen)
		
		conf['sensors'] = conf_sensors
		
		actions = self.db.session.query(Action).join((Worker, Action.workers)).filter(Worker.id == pi_id).filter(Action.active_state == True).all()
		# if we have actions we are also active
		if(len(actions)>0):
			conf['active'] = True
			
		conf_actions = []
		# iterate over all actions
		for act in actions:
			para = {}
			# create params array
			for p in act.params:
				para[p.key] = p.value
				
			conf_act = {
				"id": act.id,
				"module": act.module,
				"class": act.cl,
				"params": para
			}
			conf_actions.append(conf_act)
		
		conf['actions'] = conf_actions

		logger.info("Generated config: %s" % conf)
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

		# Help a bit to completely terminate the AMQP connection.
		# TODO: Probably the root cause for this is elsewhere. Investigate.
		sys.exit(130)


def main():
	options = parse_cmd_args()
	setup_logging(level=logging.DEBUG, config_file=options.logging_config, log_file=options.log_file)
	run_manager(options)
	logging.shutdown()


if __name__ == '__main__':
	main()

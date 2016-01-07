#!/usr/bin/env python

import datetime
import importlib
import json
import logging
import logging.config
import os
import pika
import shutil
import socket
import sys
import threading
import time

from tools import config
from tools import utils

class Worker:

	def __init__(self):
		self.actions = []
		self.sensors = []
		self.active = True # start deactivated --> only for debug True
		self.data_directory = "/var/tmp/secpi/worker_data"
		self.zip_directory = "/var/tmp/secpi"
		self.message_queue = [] # stores messages which couldn't be sent

		try: #TODO: this should be nicer...		
			logging.config.fileConfig(os.path.join(PROJECT_PATH, 'logging.conf'), defaults={'logfilename': 'worker.log'})
		except Exception, e:
			print "Error while trying to load config file for logging"

		logging.info("Initializing worker")

		try:
			config.load("worker")
			logging.debug("Config loaded")
		except ValueError: # Config file can't be loaded, e.g. no valid JSON
			logging.error("Wasn't able to load config file, exiting...")
			quit()
				
		self.prepare_data_directory(self.data_directory)
		
		self.connect()

		logging.info("Setting up sensors and actions")
		self.setup_sensors()
		self.setup_actions()
		
		logging.info("Setup done!")
	
	# sends a message to the manager
	def push_msg(self, rk, body, **kwargs):
		if self.connection.is_open:
			try:
				logging.debug("Sending message to manager")
				self.channel.basic_publish(exchange='manager', routing_key=rk, body=body, **kwargs)
				return True
			except Exception as e:
				logging.exception("Error while sending data to queue:\n%s" % e)
				return False
		else:
			logging.error("Can't send message to manager")
			message = {"rk":rk, "body": body, "kwargs": kwargs}
			if message not in self.message_queue: # could happen if we have another disconnect when we try to clear the message queue
				self.message_queue.append(message)
				logging.info("Added message to message queue")
			else:
				logging.debug("Message already in queue")

			return False

	# Try to resend the messages which couldn't be sent before
	def clear_message_queue(self):
		logging.info("Trying to clear message queue")
		for message in self.message_queue:
			if self.push_msg(message["rk"], message["body"], **message["kwargs"]): # if message was sent successfuly
				self.message_queue.remove(message)
			else:
				logging.info("Message from queue couldn't be sent")

		if not self.message_queue: # message queue is empty
			logging.info("Message queue cleared")
		else:
			logging.error("Message queue couldn't be cleared completely")
			
	def post_err(self, msg):
		logging.exception(msg)
		err = { "msg": msg,
				"level": utils.LEVEL_ERR,
				"sender": "Worker %s"%config.get('pi_id'),
				"datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
				
		properties = pika.BasicProperties(content_type='application/json')
		self.push_msg("log", json.dumps(err), properties=properties)
		
	def post_log(self, msg, lvl):
		logging.exception(msg)
		lg = { "msg": msg,
				"level": lvl,
				"sender": "Worker %s"%config.get('pi_id'),
				"datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
				
		properties = pika.BasicProperties(content_type='application/json')
		self.push_msg("log", json.dumps(lg), properties=properties)
	
	# Create a zip of all the files which were collected while actions were executed
	def prepare_data(self):
		try:
			if os.listdir(self.data_directory): # check if there are any files available
				shutil.make_archive("%s/%s" % (self.zip_directory, config.get('pi_id')), "zip", self.data_directory)
				logging.info("Created ZIP file")
				return True
			else:
				logging.info("No data to zip")
				return False
		except OSError, e:
			self.post_err("Pi with id '%s' wasn't able to prepare data for manager:\n%s" % (config.get('pi_id'), e))
			logging.error("Wasn't able to prepare data for manager: %s" % e)

	# Remove all the data that was created during the alarm, unlink == remove
	def cleanup_data(self):
		try:
			os.unlink("%s/%s.zip" % (self.zip_directory, config.get('pi_id')))
			for the_file in os.listdir(self.data_directory):
				file_path = os.path.join(self.data_directory, the_file)
				if os.path.isfile(file_path):
					os.unlink(file_path)
				elif os.path.isdir(file_path):
					shutil.rmtree(file_path)
			logging.info("Cleaned up files")
		except OSError, e:
			self.post_err("Pi with id '%s' wasn't able to execute cleanup:\n%s" % (config.get('pi_id'), e))
			logging.error("Wasn't able to clean up data directory: %s" % e)

	# callback method which processes the actions which originate from the manager
	def got_action(self, ch, method, properties, body):
		if(self.active):
			msg = json.loads(body)
			late_arrival = utils.check_late_arrival(datetime.datetime.strptime(msg["datetime"], "%Y-%m-%d %H:%M:%S"))
			
			if late_arrival:
				logging.info("Received old action from manager:%s" % body)
				return # we don't have to send a message to the data queue since the timeout will be over anyway
			# DONE: threading
			# http://stackoverflow.com/questions/15085348/what-is-the-use-of-join-in-python-threading
			logging.info("Received action from manager:%s" % body)
			threads = []
			
			for act in self.actions:
				t = threading.Thread(name='thread-%s'%(act.id), target=act.execute)
				threads.append(t)
				t.start()
				# act.execute()
		
			# wait for threads to finish
			#TODO: think about timeout, also regarding speakers	
			for t in threads:
				t.join()
		
			if self.prepare_data(): #check if there is any data to send
				zip_file = open("%s/%s.zip" % (self.zip_directory, config.get('pi_id')), "rb")
				byte_stream = zip_file.read()
				self.push_msg("data", byte_stream)
				logging.info("Sent data to manager")
				self.cleanup_data()
			else:
				logging.info("No data to send")
				# Send empty message which acts like a finished
				self.push_msg("data", "")
			# TODO: send finished
		else:
			logging.debug("Received action but wasn't active")

	def got_config(self, ch, method, properties, body):
		logging.info("Received config %r" % (body))
		
		try:
			new_conf = json.loads(body)
		except Exception, e:
			logging.exception("Wasn't able to read JSON config from manager:\n%s" % e) 
		
		# check if new config changed
		if(new_conf != config.getDict()):
			# disable while loading config
			self.active = False
			
			# TODO: deactivate queues
			self.cleanup_sensors()
			self.cleanup_actions()
			
			# TODO: check valid config file?!
			# write config to file
			try:
				f = open('%s/worker/config.json'%(PROJECT_PATH),'w') # TODO: pfad
				f.write(body)
				f.close()
			except Exception, e:
				logging.exception("Wasn't able to write config file:\n%s" % e)
			
			# set new config
			config.load("worker")
			
			if(config.get('active')):
				self.setup_sensors()
				self.setup_actions()
				# TODO: activate queues
				self.active = True
			
			logging.info("Config saved...")
		else:
			logging.info("Config didn't change")
		
	# Initialize all the sensors for operation and add callback method
	# TODO: check for duplicated sensors
	def setup_sensors(self):
		# self.sensors = []
		for sensor in config.get("sensors"):
			try:
				logging.info("Trying to register sensor: %s" % sensor["id"])
				s = self.class_for_name(sensor["module"], sensor["class"])
				sen = s(sensor["id"], sensor["params"], self)
				sen.activate()
			except Exception, e:
				self.post_err("Pi with id '%s' wasn't able to register sensor '%s':\n%s" % (config.get('pi_id'), sensor["class"],e))
			else:
				self.sensors.append(sen)
				logging.info("Registered!")
	
	def cleanup_sensors(self):
		# remove the callbacks
		for sensor in self.sensors:
			sensor.deactivate()
			logging.debug("Removed sensor: %d" % int(sensor.id))
		
		self.sensors = []
	
	# see: http://stackoverflow.com/questions/1176136/convert-string-to-python-class-object
	def class_for_name(self, module_name, class_name):
		try:
			# load the module, will raise ImportError if module cannot be loaded
			m = importlib.import_module(module_name)
			# get the class, will raise AttributeError if class cannot be found
			c = getattr(m, class_name)
			return c
		except ImportError as ie:
			self.post_err("Couldn't import module %s: %s"%(module_name, ie))
		except AttributeError as ae:
			self.post_err("Couldn't find class %s: %s"%(class_name, ae))
	
	
	# Initialize all the actions
	def setup_actions(self):
		if not config.get("actions"):
			return
		for action in config.get("actions"):
			try:
				logging.info("Trying to register action: %s" % action["id"])
				a = self.class_for_name(action["module"], action["class"])
				act = a(action["id"], action["params"])
			except Exception, e: #AttributeError, KeyError
				self.post_err("Pi with id '%s' wasn't able to register action '%s':\n%s" % (config.get('pi_id'), action["class"],e))
			else:
				self.actions.append(act)
				logging.info("Registered!")
	
	def cleanup_actions(self):
		for a in self.actions:
			a.cleanup()
			
		self.actions = []					


	# callback for the sensors, sends a message with info to the manager
	def alarm(self, sensor_id, message):
		if(self.active):
			logging.info("Sensor with id %s detected something" % sensor_id)

			msg = {	"pi_id":config.get("pi_id"),
					"sensor_id": sensor_id,
					"message": message,
					"datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
			
			msg_string = json.dumps(msg)
			
			# send a message to the alarmQ and tell which sensor signaled
			properties = pika.BasicProperties(content_type='application/json')
			self.push_msg('alarm', msg_string, properties=properties)
		
		
	def get_ip(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect((config.get("rabbitmq")["master_ip"],5672))
		ip = s.getsockname()[0]
		print(ip)
		s.close()
		
		return ip

	def prepare_data_directory(self, data_path):
		try:
			if not os.path.isdir(data_path): #check if directory structure already exists
				os.makedirs(data_path)
				logging.debug("Created SecPi data directory")
		except OSError, e:
			self.post_err("Pi with id '%s' wasn't able to create data directory:\n%s" % (config.get('pi_id'), e))

	def start(self):
		disconnected = True
		while disconnected:
			try:
				disconnected = False
				self.channel.start_consuming() # blocking call
			except pika.exceptions.ConnectionClosed: # when connection is lost, e.g. rabbitmq not running
				logging.error("Lost connection to manager")
				disconnected = True
				self.wait(10) # reconnect timer
				self.connect()
				self.clear_message_queue() #could this make problems if the manager replies too fast?
	
	def connection_cleanup(self): # not used yet
		self.channel.close()
		self.connection.close()

	def connect(self):
		#logging.info("Setting up queues")
		logging.debug("Initalizing network connection")
		credentials = pika.PlainCredentials(config.get('rabbitmq')['user'], config.get('rabbitmq')['password'])
		parameters = pika.ConnectionParameters(credentials=credentials,
			host=config.get('rabbitmq')['master_ip'], #this will change because we need the ip initially
			port=5671,
			ssl=True,
			socket_timeout=10,
			ssl_options = { 
				"ca_certs":PROJECT_PATH+"/certs/"+config.get('rabbitmq')['cacert'],
				"certfile":PROJECT_PATH+"/certs/"+config.get('rabbitmq')['certfile'],
				"keyfile":PROJECT_PATH+"/certs/"+config.get('rabbitmq')['keyfile']
			}
		)

		connected = False
		while not connected: #retry if establishing a connection fails
			try:
				logging.info("Trying to establish a connection to the manager")
				self.connection = pika.BlockingConnection(parameters=parameters) 
				self.channel = self.connection.channel()
				connected = True
				logging.info("Connection to manager established")
			except pika.exceptions.AMQPConnectionError, e: # if connection can't be established
				logging.error("Wasn't able to open a connection to the manager: %s" % e)
				self.wait(30)

		self.channel.exchange_declare(exchange='manager', exchange_type='direct')

		#declare all the queues
		self.channel.queue_declare(queue=str(config.get('pi_id'))+utils.QUEUE_ACTION)
		self.channel.queue_declare(queue=str(config.get('pi_id'))+utils.QUEUE_CONFIG)
		self.channel.queue_declare(queue=utils.QUEUE_DATA)
		self.channel.queue_declare(queue=utils.QUEUE_ALARM)
		self.channel.queue_declare(queue=utils.QUEUE_LOG)

		#specify the queues we want to listen to, including the callback
		self.channel.basic_consume(self.got_action, queue=str(config.get('pi_id'))+utils.QUEUE_ACTION, no_ack=True)
		self.channel.basic_consume(self.got_config, queue=str(config.get('pi_id'))+utils.QUEUE_CONFIG, no_ack=True)

	def wait(self, waiting_time):
		logging.debug("Waiting for %d seconds" % waiting_time)
		time.sleep(waiting_time)
	
	def __del__(self):
		try:
			self.connection.close()
		except AttributeError: #If there is no connection object closing won't work
			logging.info("No connection cleanup possible")


if __name__ == '__main__':
	w = None
	try:
		if(len(sys.argv)>1):
			PROJECT_PATH = sys.argv[1]
			w = Worker()
			w.start()
		else:
			print("Error initializing Worker, no path given!");
	except KeyboardInterrupt:
		logging.info('Shutting down worker!')
		# TODO: cleanup?
		w.cleanup_actions()
		w.cleanup_sensors()
		try:
			sys.exit(0)
		except SystemExit:
			os._exit(0)

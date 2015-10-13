import importlib
import json
import logging
import logging.config
import os
import pika
import RPi.GPIO as GPIO
import shutil
import socket
import sys
import threading
import time

from tools import config
from webcam import Webcam

class Worker:

	def __init__(self):
		self.actions = []
		self.sensors = []
		self.active = True # start deactivated --> only for debug True
		self.data_directory = "/var/tmp/secpi_data"
		
		config.load("worker")
		
		# setup gpio and logging
		GPIO.setmode(GPIO.BCM)
		logging.config.fileConfig(os.path.join(config.get('project_path'), 'logging.conf'), defaults={'logfilename': os.path.join(config.get('project_path'),'logs/worker.log')})
		
		self.prepare_data_directory(self.data_directory)

		
		logging.info("Setting up queues")
		credentials = pika.PlainCredentials(config.get('rabbitmq')['user'], config.get('rabbitmq')['password'])
		parameters = pika.ConnectionParameters(credentials=credentials,
			host=config.get('rabbitmq')['master_ip'], #this will change because we need the ip initially
			port=5671,
			ssl=True,
			socket_timeout=10,
			ssl_options = { "ca_certs":(config.get("project_path"))+config.get('rabbitmq')['cacert'],
				"certfile":config.get("project_path")+config.get('rabbitmq')['certfile'],
				"keyfile":config.get("project_path")+config.get('rabbitmq')['keyfile']
			}
		) 
		self.connection = pika.BlockingConnection(parameters=parameters) 
		self.channel = self.connection.channel()

		#declare all the queues
		self.channel.queue_declare(queue='%i_action' % config.get('pi_id'))
		self.channel.queue_declare(queue='%i_config' % config.get('pi_id'))
		self.channel.queue_declare(queue='data')
		self.channel.queue_declare(queue='alarm')
		self.channel.queue_declare(queue='error')

		#specify the queues we want to listen to, including the callback
		self.channel.basic_consume(self.got_action, queue='%i_action' % config.get('pi_id'), no_ack=True)
		self.channel.basic_consume(self.got_config, queue='%i_config' % config.get('pi_id'), no_ack=True)

		logging.info("Setting up sensors and actions")
		self.setup_sensors()
		self.setup_actions()
		
		logging.info("Setup done!")
		
		self.channel.start_consuming() # this is a blocking call!!
		
	# Create a zip of all the files which were collected while actions were executed
	def prepare_data(self):
		try:
			if os.listdir(self.data_directory): # check if there are any files available
				shutil.make_archive("/var/tmp/%s" % config.get('pi_id'), "zip", self.data_directory)
				logging.info("Created ZIP file")
				return True
			else:
				logging.info("No data to zip")
				return False
		except OSError, e:
			logging.exception("Error while trying to prepare data for manager:\n%s" % e)
			#return False

	# Remove all the data that was created during the alarm, unlink == remove
	def cleanup_data(self):
		try:
			os.unlink("/var/tmp/%s.zip" % config.get('pi_id'))
			for the_file in os.listdir(self.data_directory):
				file_path = os.path.join(self.data_directory, the_file)
				if os.path.isfile(file_path):
					os.unlink(file_path)
				elif os.path.isdir(file_path):
					shutil.rmtree(file_path)
			logging.info("Cleaned up files")
		except OSError, e:
			logging.exception("Error while cleaning up data:\n%s" % e)

	# callback method which processes the actions which originate from the manager
	def got_action(self, ch, method, properties, body):
		if(self.active):			
			# DONE: threading
			# http://stackoverflow.com/questions/15085348/what-is-the-use-of-join-in-python-threading
			logging.info("Received action from manager")
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
				zip_file = open("/var/tmp/%s.zip" % config.get('pi_id'), "rb")
				byte_stream = zip_file.read()
				self.channel.basic_publish(exchange='manager', routing_key="data", body=byte_stream)
				logging.info("Sent data to manager")
				self.cleanup_data()
			else:
				logging.info("No data to send")
				# Send empty message which acts like a finished
				self.channel.basic_publish(exchange='manager', routing_key="data", body="")
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
				f = open('config.json','w') # TODO: pfad
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
				logging.exception("Wasn't able to add sensor %r" % sensor)
				# prepare full message here, manager shouldn't have to deal with this
				error_string = "Pi with id '%s' wasn't able to register sensor '%s':\n%s" % (config.get('pi_id'), sensor["class"],e)
				self.channel.basic_publish(exchange='manager', routing_key="error", body=error_string)
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
		# TODO: try/catch
		# load the module, will raise ImportError if module cannot be loaded
		m = importlib.import_module(module_name)
		# get the class, will raise AttributeError if class cannot be found
		c = getattr(m, class_name)
		return c
	
	
	# Initialize all the actions
	def setup_actions(self):
		for action in config.get("actions"):
			try:
				logging.info("Trying to register action: %s" % action["id"])
				a = self.class_for_name(action["module"], action["class"])
				act = a(action["id"], action["params"])
			except Exception, e:
				logging.exception("Wasn't able to add action %r" % action)
				error_string = "Pi with id '%s' wasn't able to register action '%s':\n%s" % (config.get('pi_id'), action["class"],e)
				self.channel.basic_publish(exchange='manager', routing_key="error", body=error_string)
			else:
				self.actions.append(act)
				logging.info("Registered!")
	
	def cleanup_actions(self):
		# TODO: maybe manual del of all actions?
		self.actions = []					


	# callback for the sensors, sends a message with info to the manager
	def alarm(self, sensor_id, message):
		if(self.active):
			logging.info("Sensor with id %s detected something" % sensor_id)

			msg = {	"pi_id":config.get("pi_id"),
					"sensor_id": sensor_id,
					"message": message}
			
			msg_string = json.dumps(msg)
			
			# send a message to the alarmQ and tell which sensor signaled
			properties = pika.BasicProperties(content_type='application/json')
			self.channel.basic_publish(exchange='manager', routing_key='alarm', body=msg_string, properties=properties)
		
		
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
			logging.exception("Error while creating data directory:\n%s" % e)
	
	def __del__(self):
		self.connection.close()
		GPIO.cleanup()


if __name__ == '__main__':
	try:
		w = Worker()
	except KeyboardInterrupt:
		logging.info('Shutting down worker!')
		# TODO: cleanup?
		try:
			sys.exit(0)
		except SystemExit:
			os._exit(0)



import pika
import time
import sys
sys.path.append('/root/SecPi/tools')
import socket
import RPi.GPIO as GPIO
import logging
import importlib
import threading
import json
import hashlib

from tools import config
from webcam import Webcam

class Worker:

	def __init__(self):
		self.actions = []
		self.active = True # start deactivated --> only for debug True
		self.current_config_hash = None
		
		# setup gpio and logging
		GPIO.setmode(GPIO.BCM)
		logging.basicConfig(format='%(asctime)s | %(levelname)s:  %(message)s', level=logging.INFO)
		
		logging.info("loading config...")
		config.load("worker")
		# TODO: generate md5 hash
		
		logging.info("setting up queues")
		credentials = pika.PlainCredentials(config.get('rabbitmq')['user'], config.get('rabbitmq')['password'])
		parameters = pika.ConnectionParameters(credentials=credentials, host=config.get('rabbitmq')['master_ip']) #this will change because we need the ip initially
		self.connection = pika.BlockingConnection(parameters=parameters) 
		self.channel = self.connection.channel()

		#declare all the queues
		self.channel.queue_declare(queue='%i_action' % config.get('pi_id'))
		self.channel.queue_declare(queue='%i_config' % config.get('pi_id'))
		self.channel.queue_declare(queue='data')
		self.channel.queue_declare(queue='alarm')

		#specify the queues we want to listen to, including the callback
		self.channel.basic_consume(self.got_action, queue='%i_action' % config.get('pi_id'), no_ack=True)
		
		self.channel.basic_consume(self.got_config, queue='%i_config' % config.get('pi_id'), no_ack=True)

		logging.info("setting up sensors and actions")
		self.setup_sensors()
		self.setup_actions()
		
		logging.info("setup done!")
		
		self.channel.start_consuming() # this is a blocking call!!
		
		
		

	def got_action(self, ch, method, properties, body):
		if(self.active):
			# TODO: create/clear alarm_data folder
			
			# DONE: threading
			#		http://stackoverflow.com/questions/15085348/what-is-the-use-of-join-in-python-threading
			logging.info("received action from manager")
			threads = []
			
			for act in self.actions:
				t = threading.Thread(name='thread-%s'%(act.id), target=act.execute)
				threads.append(t)
				t.start()
				# act.execute()
		
			# wait for threads to finish	
			for t in threads:
				t.join()
		
			# TODO: get contents from alarm_data folder and send them over queue
			# TODO: send finished
		else:
			logging.debug("received action but wasn't active")

	def got_config(self, ch, method, properties, body):
		logging.info("received config %r" % (body))
		
		# check hash of config to detect if new
		m = hashlib.md5()
		m.update(body)
		# m.digest()
		
		# check if no hash exists (we don't have a config yet) or hash has changed (new config)
		if(self.current_config_hash is None or self.current_config_hash != m.digest()):
			# disable while loading config
			self.active = false
			
			# TODO: deactivate queues
			self.cleanup_sensors()
			
			# TODO: check valid config file?!
			# write config to file
			f = open('config.json','w') # TODO: pfad
			f.write(body)
			f.close()
			
			# set new config
			config.load("worker")
			
			if(config.get('active')):
				self.setup_sensors()
				self.setup_actions()
				# TODO: activate queues
				self.active = True
			
			logging.info("Config saved...")
		else:
			logging.info("config the same")
		
	# Initialize all the sensors for operation and add callback method
	def setup_sensors(self):
		for sensor in config.get("sensors"):
			GPIO.setup(int(sensor["gpio"]), GPIO.IN)
			GPIO.add_event_detect(int(sensor["gpio"]), GPIO.RISING, callback=self.alarm, bouncetime=5000)		
			logging.info("Registered sensor gpio: %s" % sensor["gpio"])
	
	def cleanup_sensors(self):
		# remove the callbacks
		for sensor in config.get("sensors"):
			GPIO.remove_event_detect(int(sensor["gpio"]))
	
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
			a = self.class_for_name(action["module"], action["class"])
			act = a(action["id"], action["params"])
			self.actions.append(act)
			logging.info("set up action %s" % action['class'])
					

	# callback for the sensors
	def alarm(self, channel):
		if(self.active):
			logging.info("Sensor at gpio %s detected something" % channel)

			# determine the id of the sensor which signaled
			sensor_id = ""
			for sensor in config.get("sensors"):
				if int(sensor["gpio"]) == channel:
					sensor_id = sensor["id"]
					break
			
			msg = {	"pi_id":config.get("pi_id"),
					"sensor_id": sensor_id,
					"gpio": channel}
			
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
	
	def __del__(self):
		self.connection.close()
		GPIO.cleanup()


if __name__ == '__main__':
	w = Worker()



import pika
import time
import sys
sys.path.append('/root/SecPi/tools')
import socket
import RPi.GPIO as GPIO
import logging
import importlib
import threading

from tools import config
from webcam import Webcam

class Worker:

	def __init__(self):
		# setup gpio and logging
		GPIO.setmode(GPIO.BCM)
		logging.basicConfig(format='%(asctime)s | %(levelname)s:  %(message)s', level=logging.INFO)
		
		config.load("worker")
		
		credentials = pika.PlainCredentials(config.get('rabbitmq')['user'], config.get('rabbitmq')['password'])
		parameters = pika.ConnectionParameters(credentials=credentials, host=config.get('rabbitmq')['master_ip']) #this will change because we need the ip initially
		self.connection = pika.BlockingConnection(parameters=parameters) 
		self.channel = self.connection.channel()

		#declare all the queues
		self.channel.queue_declare(queue='%s_action' % config.get('pi_id'))
		self.channel.queue_declare(queue='%s_config' % config.get('pi_id'))
		self.channel.queue_declare(queue='data')
		self.channel.queue_declare(queue='alarm')

		#specify the queues we want to listen to, including the callback
		self.channel.basic_consume(self.got_action,
							  queue='%s_action' % config.get('pi_id'),
							  no_ack=True)
		
		self.channel.basic_consume(self.got_config,
							  queue='%s_config' % config.get('pi_id'),
							  no_ack=True)

		self.actors = []
		self.setup_sensors()
		self.setup_actors()
		self.channel.start_consuming()
		

	def got_action(self, ch, method, properties, body):
		# TODO: create/clear alarm_data folder
		
		# DONE: threading
		#		http://stackoverflow.com/questions/15085348/what-is-the-use-of-join-in-python-threading
		threads = []
		
		for act in self.actors:
			t = threading.Thread(name='thread-%s'%(act.id), target=act.execute)
			threads.append(t)
			t.start()
			# act.execute()
	
		# wait for threads to finish	
		for t in threads:
			t.join()
	
		# TODO: get contents from alarm_data folder and send them over queue
		# TODO: send finished

	def got_config(self, ch, method, properties, body):
		print " [x] Received config %r" % (body,)
		# TODO: check valid config file?!
		# write config to file
		f = open('config.json','w')
		f.write(body)	
		f.close()
		# set new config
		# config.load()
		self.conf = config.getDict()
		print "Config saved..."
		
	# Initialize all the sensors for operation and add callback method
	def setup_sensors(self):
		for sensor in config.get("sensors"):
			GPIO.setup(int(sensor["gpio"]), GPIO.IN)
			GPIO.add_event_detect(int(sensor["gpio"]), GPIO.RISING, callback=self.alarm, bouncetime=5000)		
			logging.info("Registered sensor gpio: %s" % sensor["gpio"])
	
	
	# see: http://stackoverflow.com/questions/1176136/convert-string-to-python-class-object
	def class_for_name(module_name, class_name):
		# TODO: try/catch
		# load the module, will raise ImportError if module cannot be loaded
		m = importlib.import_module(module_name)
		# get the class, will raise AttributeError if class cannot be found
		c = getattr(m, class_name)
		return c
	
	# Initialize all the actors
	def setup_actors(self):
		# TODO replace self.conf 
		for actor in config.get("actors"):
			a = class_for_name(actor["module"], actor["class"])
			act = a(actor["id"], actor["params"])
			self.actors.append(act)
			#if actor["type"] == "webcam":
			#	self.actors.append(Webcam("/dev/video0", (640,480)))
					

	# callback for the sensors
	def alarm(self, channel):
		logging.info("Sensor at gpio %s detected something" % channel)

		# determine the id of the sensor which signaled
		sensor_id = ""
		for sensor in config.get("sensors"):
			if int(sensor["gpio"]) == channel:
				sensor_id = sensor["id"]	

		# send a message to the alarmQ and tell which sensor signaled
		self.channel.basic_publish(exchange='manager', routing_key='alarm',
							body="%s" % sensor_id)
		
		
	def get_ip(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect((config.get("rabbitmq")["master_ip"],5672))
		ip = s.getsockname()[0]
		print(ip)
		s.close()
		
		return ip



if __name__ == '__main__':
	w = Worker()



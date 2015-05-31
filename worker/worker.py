import pika
import time
import sys
sys.path.append('/root/SecPi/tools')
import config
import RPi.GPIO as GPIO
import logging
from webcam import Webcam

class Worker:

	def __init__(self):
		# setup gpio and logging
		GPIO.setmode(GPIO.BCM)
		logging.basicConfig(format='%(asctime)s | %(levelname)s:  %(message)s', level=logging.INFO)

		# load configuration file
		self.conf = config.getDict()

		self.connection = pika.BlockingConnection(pika.ConnectionParameters(
				host=self.conf['master_IP'])) #this will change because we need the ip initially
		self.channel = self.connection.channel()

		#declare all the queues
		self.channel.queue_declare(queue='%s_action' % self.conf['pi_id'])
		self.channel.queue_declare(queue='%s_config' % self.conf['pi_id'])
		self.channel.queue_declare(queue='data')
		self.channel.queue_declare(queue='alarm')

		#specify the queues we want to listen to, including the callback
		self.channel.basic_consume(self.got_action,
							  queue='%s_action' % self.conf['pi_id'],
							  no_ack=True)
		
		self.channel.basic_consume(self.got_config,
							  queue='%s_config' % self.conf['pi_id'],
							  no_ack=True)

		self.actors = []
		self.setup_sensors()
		self.setup_actors()
		self.channel.start_consuming()
		

	def got_action(self, ch, method, properties, body):
		# TODO: really interpret the action
		print " [x] Received action %r" % (body,)
		if "picture" in body:
			for actor in self.actors:
				actor.take_picture()
				logging.info("Webcam took a picture")
#			channel.basic_publish(exchange='manager', routing_key='data', body="BLOB")

	def got_config(self, ch, method, properties, body):
		print " [x] Received config %r" % (body,)
		# write config to file
		f = open('config.json','w')
		f.write(body)	
		f.close()
		# set new config
		self.conf = config.getDict()
		print "Config saved..."
		
	# Initialize all the sensors for operation and add callback method
	def setup_sensors(self):
		for sensor in self.conf["sensors"]:
			GPIO.setup(int(sensor["gpio"]), GPIO.IN)
			GPIO.add_event_detect(int(sensor["gpio"]), GPIO.RISING, callback=self.alarm,
														bouncetime=5000)		
			logging.info("Registered sensor gpio: %s" % sensor["gpio"])
	
	# Initialize all the actors
	def setup_actors(self):
		#TODO: initialize the actors according to their type, use more config params
		for actor in self.conf["actors"]:
			if actor["type"] == "webcam":
				self.actors.append(Webcam("/dev/video0", (640,480)))
					

	# callback for the sensors
	def alarm(self, channel):
		logging.info("Sensor at gpio %s detected something" % channel)

		# determine the id of the sensor which signaled
		sensor_id = ""
		for sensor in self.conf["sensors"]:
			if int(sensor["gpio"]) == channel:
				sensor_id = sensor["id"]	

		# send a message to the alarmQ and tell which sensor signaled
		self.channel.basic_publish(exchange='manager', routing_key='alarm',
							body="%s" % sensor_id)
		

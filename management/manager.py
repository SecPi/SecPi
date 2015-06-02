import pika
import time
import sys
import logging
import json

from tools.db import database as db
from tools import config

#state = False
#
#def init():
#	# register cb_onoff
#	check_setups()
#
#def check_setups():
#	# TODO: check if active setup is the same
#	setups = get_active_setups()
#	if(len(setups)>0):
#		if(not state):
#			state = True
#			send_config(True)
#	else:
#		if(state):
#			state = False
#			send_config(False)
#
#def get_active_setups():
#	# get stuff from db
#	
#	
#def send_config(new_state):
#	# get stuff from db
#	# convert stuff to json
#	# send stuff over queue to worker
#
#def cb_onoff():
#	check_setups()
#	
#def cb_data():
#	# wait for data
#


class Manager:

	def __init__(self):
		logging.basicConfig(format='%(asctime)s | %(levelname)s:  %(message)s', level=logging.INFO)	# TODO make it nicer
		
		config.load("management")
		db.connect()
		
		credentials = pika.PlainCredentials(config.get('rabbitmq')['user'], config.get('rabbitmq')['password'])
		parameters = pika.ConnectionParameters(credentials=credentials, host=config.get('rabbitmq')['master_ip'])
		self.connection = pika.BlockingConnection(parameters=parameters)
		self.channel = self.connection.channel()

		#define exchange
		self.channel.exchange_declare(exchange='manager', exchange_type='direct')


		#define queues: data, alarm and action & config for every pi
		self.channel.queue_declare(queue='data')
		self.channel.queue_declare(queue='alarm')
		self.channel.queue_declare(queue='register')
		self.channel.queue_bind(exchange='manager', queue='data')
		self.channel.queue_bind(exchange='manager', queue='alarm')
		self.channel.queue_bind(exchange='manager', queue='register')
		
		# load workers from db
		workers = db.session.query(db.objects.Worker).all()
		for pi in workers:
			self.channel.queue_declare(queue='%i_action'%pi.id)
			self.channel.queue_declare(queue='%i_config'%pi.id)
			self.channel.queue_bind(exchange='manager', queue='%i_action'%pi.id)
			self.channel.queue_bind(exchange='manager', queue='%i_config'%pi.id)

		#define callbacks for alarm and data queues
		self.channel.basic_consume(self.got_alarm, queue='alarm', no_ack=True)
		self.channel.basic_consume(self.cb_register, queue='register', no_ack=True)
		#self.channel.basic_consume(self.got_data, queue='data', no_ack=True)

		self.channel.start_consuming()

	


	def send_message(self, to_queue, message):
		self.channel.basic_publish(exchange='manager', routing_key=to_queue, body=message)
		logging.info("Sending Action to rpi")


	def got_alarm(self, ch, method, properties, body):
		'''
			json:
			{
				"pi_id": 12,
				"sensor_id": 123
				"gpio": 16
			}
			then select from sensors s join workers w on s.worker_id = w.id where w.id = pi_id and s.gpio_pin = 16
		'''
		logging.info("received alarm: %s"%body)
		
		msg = json.loads(body)
		
		# TODO: check if last alarm more then x seconds ago
		# interate over workers and send "execute"
		workers = db.session.query(db.objects.Worker).all()
		for pi in workers:	
			self.send_message("%i_action"%pi.id, "execute")
		
		
		al = db.objects.Alarm(sensor_id=msg['sensor_id'])
		lo = db.objects.LogEntry(level=db.objects.LogEntry.LEVEL_INFO, message="New Alarm from %s on Sensor %s (GPIO Pin %s)"%(msg['pi_id'], msg['sensor_id'], msg['gpio']))
		db.session.add(al)
		db.session.add(lo)
		db.session.commit()


	# TODO send config
	def send_actions(self, pi_id):
		actions = db.session.query(db.objects.Action).join(db.objects.Worker).filter(Worker.id==pi_id).all()
		
		js = json.dumps(a.__dict__ for a in actions)
		print(js)
		

	def cb_register(self, ch, method, properties, body):
		'''Wait for new workers to register.'''
	
	def __del__(self):
		self.connection.close()


	# wait for config
	# or queue
	# if setup active in db && not active
	# 	send activate, config etc.
	# else if no setup active in db && active
	# 	send deactivate

if __name__ == '__main__':
    mg = Manager()

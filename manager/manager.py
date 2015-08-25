import hashlib
import json
import logging
import pika
import sys
import time

from mailer import Mailer
from tools import config
from tools.db import database as db

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
		
		config.load("manager")
		db.connect()
		
		credentials = pika.PlainCredentials(config.get('rabbitmq')['user'], config.get('rabbitmq')['password'])
		parameters = pika.ConnectionParameters(credentials=credentials, host=config.get('rabbitmq')['master_ip'])
		self.connection = pika.BlockingConnection(parameters=parameters)
		self.channel = self.connection.channel()

		# TODO: read config from db or config file?
		self.mailer = Mailer(config.get('mail')['sender'], config.get('mail')['recipient'],
							 config.get('mail')['subject'], config.get('mail')['text'],
							 config.get('mail')['data_dir'], config.get('mail')['smtp_address'],
							 config.get('mail')['smtp_port'], config.get('mail')['smtp_user'],
							 config.get('mail')['smtp_pass'], config.get('mail')['smtp_security'])

		#define exchange
		self.channel.exchange_declare(exchange='manager', exchange_type='direct')

		#define queues: data, alarm and action & config for every pi
		self.channel.queue_declare(queue='data')
		self.channel.queue_declare(queue='alarm')
		self.channel.queue_declare(queue='register')
		self.channel.queue_declare(queue='on_off')
		self.channel.queue_bind(exchange='manager', queue='on_off')
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
		self.channel.basic_consume(self.cb_on_off, queue='on_off', no_ack=True)
		self.channel.basic_consume(self.got_data, queue='data', no_ack=True)
		logging.info("Setup done!")

	
	def start(self):
		self.channel.start_consuming()
	
	def got_data(self, ch, method, properties, body):
		logging.info("Got data")
		newFile_bytes = bytearray(body)
		newFile = open("/var/tmp/manager/%s.zip" % hashlib.md5(newFile_bytes).hexdigest(), "wb")
		newFile.write(newFile_bytes)
		logging.info("Data written")

		# JFT: move mail sending to got_alarm
		#self.mailer.send_mail()
		# TODO: data has to be moved somewhere else or deleted, after mail has been sent


	def cb_on_off(self, ch, method, properties, body):
		msg = json.loads(body)
			
		logging.info("Activating PIs!")
		workers = db.session.query(db.objects.Worker).filter(db.objects.Worker.active_state == True).all()
		for pi in workers:
			self.send_config(pi.id)
			logging.info("Activated %s"%pi.name)

	def send_message(self, to_queue, message):
		self.channel.basic_publish(exchange='manager', routing_key=to_queue, body=message)
		logging.info("Sending action to %s"%to_queue)


	def got_alarm(self, ch, method, properties, body):
		logging.info("Received alarm: %s"%body)
		
		msg = json.loads(body)
		
		# TODO: check if last alarm more then x seconds ago
		# interate over workers and send "execute"
		workers = db.session.query(db.objects.Worker).filter(db.objects.Worker.active_state == True).all()
		for pi in workers:
			self.send_message("%i_action"%pi.id, "execute")
		
		al = db.objects.Alarm(sensor_id=msg['sensor_id'])
		lo = db.objects.LogEntry(level=db.objects.LogEntry.LEVEL_INFO, message="New alarm from %s on sensor %s (GPIO Pin %s)"%(msg['pi_id'], msg['sensor_id'], msg['gpio']))
		db.session.add(al)
		db.session.add(lo)
		db.session.commit()
		# TODO: wait until all workers finished with their actions then send mail etc


	
	def send_config(self, pi_id):
		conf = {
			"pi_id": pi_id,
			"rabbitmq": config.get("rabbitmq"),
			"holddown": 30, # TODO: save somewhere? include for worker?
			"active": False, # default to false, will be overriden if should be true
		}
		
		sensors = db.session.query(db.objects.Sensor).join(db.objects.Zone).join((db.objects.Setup, db.objects.Zone.setups)).filter(db.objects.Setup.active_state == True).filter(db.objects.Sensor.worker_id == pi_id).all()
		
		# if we have sensors we are active
		if(len(sensors)>0):
			conf['active'] = True
		
		
		conf_sensors = []
		for sen in sensors:
			conf_sen = {
				"id": sen.id,
				"gpio": sen.gpio_pin,
				"name": sen.name
			}
			conf_sensors.append(conf_sen)
		
		conf['sensors'] = conf_sensors
		
		actions = db.session.query(db.objects.Action).join((db.objects.Worker, db.objects.Action.workers)).filter(db.objects.Worker.id == pi_id).all()
		# if we have actions we are also active
		if(len(actions)>0):
			conf['active'] = True
			
		conf_actions = []
		# iterate over all actions
		for act in actions:
			# get params for action
			params = db.session.query(db.objects.ActionParam).filter(db.objects.ActionParam.action_id == act.id).all()
			para = {}
			# create params array
			for p in params:
				para[p.key] = p.value
				
			conf_act = {
				"id": act.id,
				"module": act.module,
				"class": act.cl,
				"params": para
			}
			conf_actions.append(conf_act)
		
		conf['actions'] = conf_actions
		
		msg = json.dumps(conf)
		logging.info("Generated config: %s" % msg)
		
		properties = pika.BasicProperties(content_type='application/json')
		self.channel.basic_publish(exchange='manager', routing_key='%i_config'%pi_id, body=msg, properties=properties)
		

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
    # mg.send_config(1)
    mg.start()

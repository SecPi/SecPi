import pika
import time
import sys
import logging

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
		logging.basicConfig(format='%(asctime)s | %(levelname)s:  %(message)s', level=logging.INFO)	
		self.list_of_pis = ['rpi', 'bpi']
		self.connection = pika.BlockingConnection(pika.ConnectionParameters(
				host = 'localhost'))
		self.channel = self.connection.channel()

		#define exchange
		self.channel.exchange_declare(exchange='manager', exchange_type='direct')


		#define queues: data, alarm and action & config for every pi
		self.channel.queue_declare(queue='data')
		self.channel.queue_declare(queue='alarm')
		self.channel.queue_bind(exchange='manager', queue='data')
		self.channel.queue_bind(exchange='manager', queue='alarm')
		for pi in self.list_of_pis:
			self.channel.queue_declare(queue='%s_action'%pi)
			self.channel.queue_declare(queue='%s_config'%pi)
			self.channel.queue_bind(exchange='manager', queue='%s_action'%pi)
			self.channel.queue_bind(exchange='manager', queue='%s_config'%pi)

		#define callbacks for alarm and data queues
		self.channel.basic_consume(self.got_alarm, queue='alarm', no_ack=True)
		#self.channel.basic_consume(self.got_data, queue='data', no_ack=True)

		self.channel.start_consuming()

	def send_action(self, to_queue, message):
		self.channel.basic_publish(exchange='manager', routing_key=to_queue, body=message)
		logging.info("Sending Action to rpi")


	def got_alarm(self, ch, method, properties, body):
		# TODO prepare actions according to the configured actors
		logging.info("Sensor with ID %s raised an alarm" % body)
		self.send_action("rpi_action", "picture")



	def destroy(self):
		self.connection.close()


if __name__ == '__main__':
    init()

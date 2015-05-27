import pika
import time
import sys

state = False

def init():
	# register cb_onoff
	check_setups()

def check_setups():
	# TODO: check if active setup is the same
	setups = get_active_setups()
	if(len(setups)>0):
		if(not state):
			state = True
			send_config(True)
	else:
		if(state):
			state = False
			send_config(False)

def get_active_setups():
	# get stuff from db
	
	
def send_config(new_state):
	# get stuff from db
	# convert stuff to json
	# send stuff over queue to worker

def cb_onoff():
	check_setups()
	

def cb_data():
	# wait for data



class Manager:

	def __init__(self):
		self.list_of_pis = ['rpi', 'bpi']
		self.connection = pika.BlockingConnection(pika.ConnectionParameters(
				host = 'localhost'))
		self.channel = self.connection.channel()

		#define exchange
		self.channel.exchange_declare(exchange='manager', exchange_type='direct')


		#define queues
		self.channel.queue_declare(queue='data')
		self.channel.queue_bind(exchange='manager', queue='data')
		for pi in self.list_of_pis:
			self.channel.queue_declare(queue='%s_action'%pi)
			self.channel.queue_declare(queue='%s_config'%pi)
			self.channel.queue_bind(exchange='manager', queue='%s_action'%pi)
			self.channel.queue_bind(exchange='manager', queue='%s_config'%pi)

	def send_action(self, to_queue, message):
		self.channel.basic_publish(exchange='manager', routing_key=to_queue, body=message)
		print "Sent '%s'" % message



#		def callback(ch, method, properties, body):
#			print "Got image: %r" % (body,)
#
#		channel.basic_consume(callback, queue='data', no_ack=True)
#		channel.start_consuming()

	def destroy(self):
		self.connection.close()


if __name__ == '__main__':
    init()
import pika
import time
import sys
sys.path.append('/root/SecPi/tools')
import config

class Worker:

	def __init__(self):
		# load configuration file
		conf = config.getDict()

		self.connection = pika.BlockingConnection(pika.ConnectionParameters(
				host=conf['master_IP'])) #this will change because we need the ip initially
		self.channel = self.connection.channel()

		#declare all the queues
		self.channel.queue_declare(queue='%s_action' % conf['pi_id'])
		self.channel.queue_declare(queue='%s_config' % conf['pi_id'])
		self.channel.queue_declare(queue='data')
		self.channel.queue_declare(queue='alarm')

		#specify the queues we want to listen to, including the callback
		self.channel.basic_consume(self.got_action,
							  queue='%s_action' % conf['pi_id'],
							  no_ack=True)
		
		self.channel.basic_consume(self.got_config,
							  queue='%s_config' % conf['pi_id'],
							  no_ack=True)

		self.channel.start_consuming()
		

	def got_action(self, ch, method, properties, body):
		print " [x] Received action %r" % (body,)
		if "picture" in body:
			print "Sending picture to master"
#			channel.basic_publish(exchange='manager', routing_key='data', body="BLOB")

	def got_config(self, ch, method, properties, body):
		print " [x] Received config %r" % (body,)
		# write config to file
		f = open('config.json','w')
		f.write(body)	
		f.close()
		print "Config saved..."
		

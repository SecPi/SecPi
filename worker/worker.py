import pika
import time
import sys

class Worker:

	def __init__(self):
		self.connection = pika.BlockingConnection(pika.ConnectionParameters(
				host='192.168.0.100'))
		self.channel = self.connection.channel()

		self.channel.queue_declare(queue='bpi_action')
		self.channel.queue_declare(queue='data')

		self.channel.basic_consume(self.got_message,
							  queue='bpi_action',
							  no_ack=True)

		self.channel.start_consuming()
		

	def got_message(self, ch, method, properties, body):
		print " [x] Received %r" % (body,)
		if "picture" in body:
			print "Sending picture to master"
#			channel.basic_publish(exchange='manager', routing_key='data', body="BLOB")

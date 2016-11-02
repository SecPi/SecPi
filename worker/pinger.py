from tools.sensor import Sensor
import logging
import pyping
import threading
import time

class Pinger(Sensor):

	def __init__(self, id, params, worker):
		super(Pinger, self).__init__(id, params, worker)
		self.interval = 5
		self.max_losses = 2
		self.destination_ip = "192.168.0.10"
		self.bouncetime = 30

		logging.info("Pinger: Sensor initialized")

	def activate(self):
		self.stop_thread = False
		self.pinger_thread = threading.Thread(name="thread-pinger-%s" % self.destination_ip,
											  target=self.check_up)
		self.pinger_thread.start()

	def deactivate(self):
		self.stop_thread = True


	def check_up(self):
		losses = 0
		while True:
			if self.stop_thread:
				return

			reply = pyping.ping(self.destination_ip) # ret value is 0 when reachable
			logging.info("ret value: %d" % reply.ret_code)
			if reply.ret_code:
				losses += 1
				logging.info("Loss happened: %d/%d" % (losses, self.max_losses))

			if losses >= self.max_losses:
				logging.info("Alarm")
				self.alarm("Too many pings lost")
				losses = 0
				time.sleep(self.bouncetime)
				continue
			time.sleep(self.interval)
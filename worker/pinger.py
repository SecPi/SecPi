from tools.sensor import Sensor
import logging
import pyping
import threading
import time

class Pinger(Sensor):

	def __init__(self, id, params, worker):
		super(Pinger, self).__init__(id, params, worker)
		
		try:
			self.interval = int(params["interval"])
			self.max_losses = int(params["max_losses"])
			self.destination_ip = params["destination_ip"]
			self.bouncetime = int(params["bounce_time"])
		except KeyError as ke: # if config parameters are missing in file
			self.post_err("Pinger: Wasn't able to initialize, it seems there is a config parameter missing: %s" % ke)
			self.corrupted = True
			return
		except ValueError as ve: # if a parameter can't be parsed as int
			self.post_err("Pinger: Wasn't able to initialize, please check your configuration: %s" % ve)
			self.corrupted = True
			return

		logging.debug("Pinger: Sensor initialized")

	def activate(self):
		if not self.corrupted:
			self.stop_thread = False
			self.pinger_thread = threading.Thread(name="thread-pinger-%s" % self.destination_ip, target=self.check_up)
			self.pinger_thread.start()
		else:
			self.post_err("Pinger: Sensor couldn't be activated")

	def deactivate(self):
		if not self.corrupted:
			self.stop_thread = True
		else:
			self.post_err("Pinger: Sensor couldn't be deactivated")


	def check_up(self):
		losses = 0
		while True:
			if self.stop_thread:
				return

			reply = pyping.ping(self.destination_ip) # ret value is 0 when reachable
			if reply.ret_code:
				losses += 1
				logging.info("Pinger: Loss happened, %d/%d" % (losses, self.max_losses))
			else:
				losses = 0

			if losses >= self.max_losses:
				self.alarm("%d consecutive pings were lost" % losses)
				losses = 0
				time.sleep(self.bouncetime)
				continue
			time.sleep(self.interval)
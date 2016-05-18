import abc
import logging

class Sensor(object):
	
	def __init__(self, id, params, worker):
		self.id = id
		self.params = params
		self.worker = worker
		self.corrupted = False
	
	def alarm(self, message):
		self.worker.alarm(self.id, message)
	
	def post_log(self, msg, lvl):
		self.worker.post_log(msg, lvl)
	
	def post_err(self, msg):
		self.worker.post_err(msg)
	
	@abc.abstractmethod
	def activate(self):
		"""Activate the sensor."""
		return

	@abc.abstractmethod
	def deactivate(self):
		"""Deactivate the sensor."""
		return
	
	
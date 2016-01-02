import abc

class Sensor(object):
	
	def __init__(self, id, params, worker):
		self.id = id
		self.params = params
		self.worker = worker
		self.corrupted = False
	
	def alarm(self, message):
		self.worker.alarm(self.id, message)
	
	@abc.abstractmethod
	def activate(self):
		"""Activate the sensor."""
		return

	@abc.abstractmethod
	def deactivate(self):
		"""Deactivate the sensor."""
		return
	
	
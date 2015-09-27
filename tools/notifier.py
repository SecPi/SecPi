import abc

class Notifier(object):

	def __init__(self, id, params):
		self.id = id
		self.params = params

	@abc.abstractmethod
	def notify(self):
		return
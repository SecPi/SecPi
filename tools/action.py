import abc

class Action(object):
	
	def __init__(self, id, params):
		self.id = id
		self.params = params
		self.corrupted = False
		
	@abc.abstractmethod
	def execute(self):
		"""Do some stuff.
		Params is a dict with additional info for the executing actor."""
		return
	
	
	@abc.abstractmethod
	def cleanup(self):
		"""Cleanup anything you might have started. (e.g. listening on ports etc.)"""
		return

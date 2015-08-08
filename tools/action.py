import abc

class Action(object):
	
	def __init__(self, id, params):
		self.id = id
		self.params = params
		
	@abc.abstractmethod
	def execute(self, data_path):
		"""Do some stuff.
		Params is a dict with additional info for the executing actor."""
		return

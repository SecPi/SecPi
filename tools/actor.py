import abc

class Actor:
	
	def __init__(self, id):
		self.id = id
		
	@abc.abstractmethod
	def execute(self, params):
		"""Do some stuff.
		Params is a dict with additional info for the executing actor."""
		return
	
	
	def finished(self):
		# send callback to manager with id
		return
	 
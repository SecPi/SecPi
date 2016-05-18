import logging

from tools.action import Action
from tools import utils

class TestAction(Action):

	def __init__(self, id, params, worker):
		super(TestAction, self).__init__(id, params, worker)

		logging.debug("Test Action initialized!")

	def execute(self):
		logging.info("Executing Test Action!")
		self.post_log("Executing Test Action!", utils.LEVEL_INFO)
		if 'msg' in self.params:
			logging.info("Test Action Message: %s"%self.params['msg'])
			self.post_log("Test Action Message: %s"%self.params['msg'], utils.LEVEL_INFO)
		
	def cleanup(self):
		logging.debug("Test Action Cleanup")
		

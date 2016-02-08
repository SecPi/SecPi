import logging

from tools.action import Action

class TestAction(Action):

	def __init__(self, id, params):
		super(TestAction, self).__init__(id, params)

		logging.debug("Test Action initialized!")

	def execute(self):
		logging.log("Executing Test Action!")
		if 'msg' in self.params:
			logging.log("Test Action Message: %s"%self.params['msg'])
		
	def cleanup(self):
		logging.debug("Test Action Cleanup")
		

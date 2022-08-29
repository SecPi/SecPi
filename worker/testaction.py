import logging

from tools.action import Action
from tools import utils


logger = logging.getLogger(__name__)


class TestAction(Action):

	def __init__(self, id, params, worker):
		super(TestAction, self).__init__(id, params, worker)

		logger.debug("Test Action initialized")

	def execute(self):
		logger.info("Executing Test Action")
		self.post_log("Executing Test Action", utils.LEVEL_INFO)
		if 'msg' in self.params:
			logger.info("Test Action Message: %s"%self.params['msg'])
			self.post_log("Test Action Message: %s"%self.params['msg'], utils.LEVEL_INFO)
		
	def cleanup(self):
		logger.debug("Test Action Cleanup")

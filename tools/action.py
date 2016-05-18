import abc
import logging
from tools import utils

class Action(object):
	
	def __init__(self, id, params, worker):
		self.id = id
		self.params = params
		self.corrupted = False
		self.worker = worker
	
	def post_log(self, msg, lvl):
		logging.info(msg)
		self.worker.post_log(msg, lvl)
	
	def post_err(self, msg):
		logging.error(msg)
		self.worker.post_err(msg)
	
	@abc.abstractmethod
	def execute(self):
		"""Do some stuff.
		Params is a dict with additional info for the executing actor."""
		return
	
	
	@abc.abstractmethod
	def cleanup(self):
		"""Cleanup anything you might have started. (e.g. listening on ports etc.)"""
		return

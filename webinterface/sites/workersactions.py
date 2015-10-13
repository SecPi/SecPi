# web framework
import cherrypy

# our stuff
from tools.db import objects
from tools import config
from tools import utils

from baserelationshippage import BaseRelationshipPage

class WorkersActionsPage(BaseRelationshipPage):
	
	def __init__(self):
		super(WorkersActionsPage, self).__init__(objects.Worker, "worker", objects.Action, "action")




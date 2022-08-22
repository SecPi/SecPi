# web framework
import cherrypy

# our stuff
from tools.db import objects
from tools import config
from tools import utils

from .baserelationshippage import BaseRelationshipPage

class SetupsZonesPage(BaseRelationshipPage):
	
	def __init__(self):
		super(SetupsZonesPage, self).__init__(objects.Setup, "setup", objects.Zone, "zone")



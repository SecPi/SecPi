from tools.db.objects import Setup, Zone
from .baserelationshippage import BaseRelationshipPage


class SetupsZonesPage(BaseRelationshipPage):
	
	def __init__(self):
		super(SetupsZonesPage, self).__init__(Setup, "setup", Zone, "zone")

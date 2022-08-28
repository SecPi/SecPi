from tools.db.objects import Worker, Action
from .baserelationshippage import BaseRelationshipPage


class WorkersActionsPage(BaseRelationshipPage):
	
	def __init__(self):
		super(WorkersActionsPage, self).__init__(Worker, "worker", Action, "action")

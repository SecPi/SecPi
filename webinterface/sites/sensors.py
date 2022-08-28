from tools.db import objects
from ..base_webpage import BaseWebPage


class SensorsPage(BaseWebPage):
	
	def __init__(self):
		super(SensorsPage, self).__init__(objects.Sensor)
		self.fields['id'] = {'name':'ID', 'visible':['list']}
		self.fields['name'] = {'name':'Name', 'visible':['list', 'add', 'update']}
		self.fields['description'] = {'name':'Description', 'visible':['list', 'add', 'update']}
		self.fields['zone_id'] = {'name':'Zone ID', 'visible':['list', 'add', 'update'], 'type': 'number'}
		self.fields['worker_id'] = {'name':'Worker ID', 'visible':['list', 'add', 'update'], 'type': 'number'}
		self.fields['cl'] = {'name':'Class', 'visible':['list', 'add', 'update']}
		self.fields['module'] = {'name':'Module', 'visible':['list', 'add', 'update']}

# web framework
import cherrypy


# our stuff
from tools.db import objects
from tools import config
from base_webpage import BaseWebPage



class SensorParamsPage(BaseWebPage):
	
	def __init__(self):
		super(SensorParamsPage, self).__init__(objects.Param)
		self.fields['id'] = {'name':'ID', 'visible':['list']}
		self.fields['object_id'] = {'name':'Object ID', 'visible':['list', 'add', 'update'], 'type':'number', 'default':0}
		self.fields['object_type'] = {'name':'Type', 'visible':['list', 'add', 'update'], 'type':'hidden', 'default':'sensor'}
		self.fields['key'] = {'name':'Key', 'visible':['list', 'add', 'update']}
		self.fields['value'] = {'name':'Value', 'visible':['list', 'add', 'update']}
		self.fields['description'] = {'name':'Description', 'visible':['list', 'add', 'update']}







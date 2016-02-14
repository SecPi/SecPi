# web framework
import cherrypy


# our stuff
from tools.db import objects
from tools import config
from base_webpage import BaseWebPage



class ActionParamsPage(BaseWebPage):
	
	def __init__(self):
		super(ActionParamsPage, self).__init__(objects.Param)
		self.fields['id'] = {'name':'ID', 'visible':['list']}
		self.fields['object_id'] = {'name':'Action ID', 'visible':['list', 'add', 'update'], 'type':'number', 'default':0}
		self.fields['object_type'] = {'name':'Type', 'visible':['add', 'update'], 'type':'hidden', 'default':'action'}
		self.fields['key'] = {'name':'Key', 'visible':['list', 'add', 'update']}
		self.fields['value'] = {'name':'Value', 'visible':['list', 'add', 'update']}
		self.fields['description'] = {'name':'Description', 'visible':['list', 'add', 'update']}







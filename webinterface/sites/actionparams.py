# web framework
import cherrypy


# our stuff
from tools.db import objects
from tools import config
from base_webpage import BaseWebPage



class ActionParamsPage(BaseWebPage):
	
	def __init__(self):
		super(ActionParamsPage, self).__init__(objects.ActionParam)
		self.fields['id'] = {'name':'ID', 'visible':['list']}
		self.fields['action_id'] = {'name':'Action ID', 'visible':['list', 'add', 'update']}
		self.fields['key'] = {'name':'Key', 'visible':['list', 'add', 'update']}
		self.fields['value'] = {'name':'Value', 'visible':['list', 'add', 'update']}
		self.fields['description'] = {'name':'Description', 'visible':['list', 'add', 'update']}


	@cherrypy.expose
	def index(self, flash_message=None):
		tmpl = self.lookup.get_template("actionparams.mako")
		return tmpl.render(page_title="Action Parameters", flash_message=flash_message)






# web framework
import cherrypy


# our stuff
from tools.db import objects
from tools import config
from base_webpage import BaseWebPage



class ActionsPage(BaseWebPage):
	
	def __init__(self):
		super(ActionsPage, self).__init__(objects.Action)
		self.fields['id'] = {'name':'ID', 'visible':['list']}
		self.fields['name'] = {'name':'Name', 'visible':['list', 'add', 'update']}
		self.fields['description'] = {'name':'Description', 'visible':['list', 'add', 'update']}
		self.fields['cl'] = {'name':'Class', 'visible':['list', 'add', 'update']}


	@cherrypy.expose
	def index(self, flash_message=None):
		tmpl = self.lookup.get_template("actions.mako")
		return tmpl.render(page_title="Actions", flash_message=flash_message)






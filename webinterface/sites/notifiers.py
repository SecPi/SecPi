# web framework
import cherrypy


# our stuff
from tools.db import objects
from tools import config
from base_webpage import BaseWebPage



class NotifiersPage(BaseWebPage):
	
	def __init__(self):
		super(NotifiersPage, self).__init__(objects.Notifier)
		self.fields['id'] = {'name':'ID', 'visible':['list']}
		self.fields['name'] = {'name':'Name', 'visible':['list', 'add', 'update']}
		self.fields['description'] = {'name':'Description', 'visible':['list', 'add', 'update']}
		self.fields['cl'] = {'name':'Class', 'visible':['list', 'add', 'update']}
		self.fields['module'] = {'name':'Module', 'visible':['list', 'add', 'update']}
		self.fields['active_state'] = {'name':'Active', 'visible':['list', 'add', 'update'], 'type':'bool'}


	@cherrypy.expose
	def index(self, flash_message=None):
		tmpl = self.lookup.get_template("notifiers.mako")
		return tmpl.render(page_title="Notifiers", flash_message=flash_message)






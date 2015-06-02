# web framework
import cherrypy


# our stuff
from tools.db import objects
from tools import config
from base_webpage import BaseWebPage



class LogEntriesPage(BaseWebPage):
	
	def __init__(self):
		super(LogEntriesPage, self).__init__(objects.LogEntry)
		self.fields['id'] = {'name':'ID', 'visible':['list']}
		self.fields['logtime'] = {'name':'Time', 'visible':['list', 'add']}
		self.fields['ack'] = {'name':'Ack', 'visible':['list', 'add']}
		self.fields['level'] = {'name':'Log Level', 'visible':['list', 'add']}
		self.fields['message'] = {'name':'Message', 'visible':['list', 'add']}
		
	@cherrypy.expose
	def index(self, flash_message=None):
		tmpl = self.lookup.get_template("logs.mako")
		return tmpl.render(page_title="Logs", flash_message=flash_message)






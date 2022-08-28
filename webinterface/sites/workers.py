import cherrypy

from tools.db.objects import Worker
from ..base_webpage import BaseWebPage


class WorkersPage(BaseWebPage):
	
	def __init__(self):
		super(WorkersPage, self).__init__(Worker)
		self.fields['id'] = {'name':'ID', 'visible':['list']}
		self.fields['name'] = {'name':'Name', 'visible':['list', 'add', 'update']}
		self.fields['address'] = {'name':'IP Address', 'visible':['list', 'add', 'update']}
		self.fields['description'] = {'name':'Description', 'visible':['list', 'add', 'update']}
		self.fields['active_state'] = {'name':'Active', 'visible':['list', 'add', 'update'], 'type':'bool'}

	@cherrypy.expose
	def index(self):
		tmpl = self.lookup.get_template("workers.mako")
		return tmpl.render(page_title="Workers")

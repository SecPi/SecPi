# web framework
import cherrypy


# our stuff
from tools.db import objects
from tools import config
from tools import utils
from base_webpage import BaseWebPage


class LogEntriesPage(BaseWebPage):
	
	def __init__(self):
		super(LogEntriesPage, self).__init__(objects.LogEntry)
		self.fields['id'] = {'name':'ID', 'visible':['list']}
		self.fields['logtime'] = {'name':'Time', 'visible':['list', 'add']}
		self.fields['ack'] = {'name':'Ack', 'visible':['list', 'add', 'update'], 'type':'bool'}
		self.fields['level'] = {'name':'Log Level', 'visible':['list', 'add']}
		self.fields['message'] = {'name':'Message', 'visible':['list', 'add']}
		
	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def ack(self):
		if(hasattr(cherrypy.request, 'json')):
			id = cherrypy.request.json['id']
			if id:
				obj = self.db.query(objects.LogEntry).get(id)
				if(obj):
					obj.ack = True;
					self.db.commit()
					return {'status': 'success', 'message': 'Acknowledged log message with id %s'%obj.id}
		
		return {'status': 'error', 'message': 'ID not found!'}
		




# web framework
import cherrypy


# our stuff
from tools.db import objects
from base_webpage import BaseWebPage

from tools import utils


class AlarmsPage(BaseWebPage):
	
	def __init__(self):
		super(AlarmsPage, self).__init__(objects.Alarm)
		self.fields['id'] = {'name':'ID', 'visible':['list']}
		self.fields['alarmtime'] = {'name':'Alarm Time', 'visible':['list']}
		self.fields['sensor_id'] = {'name':'Sensor ID', 'visible':['list', 'add']}
		self.fields['ack'] = {'name':'Ack.', 'visible':['list', 'add', 'update'], 'type':'bool'}
		self.fields['message'] = {'name':'Message', 'visible':['list', 'add']}
		#self.fields['active'] = {'name':'Active', 'visible':['list', 'add', 'update']}


	@cherrypy.expose
	def index(self, flash_message=None):
		tmpl = self.lookup.get_template("alarms.mako")
		return tmpl.render(page_title="Alarms", flash_message=flash_message)

	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def ack(self):
		if(hasattr(cherrypy.request, 'json')):
			id = cherrypy.request.json['id']
			if id:
				obj = self.db.query(objects.Alarm).get(id)
				if(obj):
					obj.ack = True;
					self.db.commit()
					return {'status': 'success', 'message': 'Acknowledged alarm with id %s'%obj.id}
		
		return {'status': 'error', 'message': 'ID not found!'}

	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def ackAll(self):
		les = self.db.query(objects.Alarm).filter(objects.Alarm.ack == 0).all()
		if(les):
			for le in les:
				le.ack = True;
				
			self.db.commit()
			return {'status': 'success', 'message': 'Acknowledged all alarms!'}
		
		return {'status': 'error', 'message': 'No alarms to acknowledge found!'}
	


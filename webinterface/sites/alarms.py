# web framework
import cherrypy


# our stuff
from tools.db import objects
from base_webpage import BaseWebPage



class AlarmsPage(BaseWebPage):
	
	def __init__(self):
		super(AlarmsPage, self).__init__(objects.Alarm)
		self.fields['id'] = {'name':'ID', 'visible':['list']}
		self.fields['alarmtime'] = {'name':'Alarm Time', 'visible':['list']}
		self.fields['sensor_id'] = {'name':'Sensor ID', 'visible':['list', 'add', 'update']}
		#self.fields['active'] = {'name':'Active', 'visible':['list', 'add', 'update']}


	@cherrypy.expose
	def index(self, flash_message=None):
		tmpl = self.lookup.get_template("alarms.mako")
		return tmpl.render(page_title="Alarms", flash_message=flash_message)






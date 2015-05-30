# web framework
import cherrypy


# our stuff
from tools.db import objects
from tools import config
from base_webpage import BaseWebPage



class SensorsPage(BaseWebPage):
	
	def __init__(self):
		super(SensorsPage, self).__init__(objects.Sensor)
		self.fields['id'] = {'name':'ID', 'visible':['list']}
		self.fields['name'] = {'name':'Name', 'visible':['list', 'add', 'update']}
		self.fields['description'] = {'name':'Description', 'visible':['list', 'add', 'update']}
		self.fields['gpio_pin'] = {'name':'GPIO Pin', 'visible':['list', 'add', 'update']}
		self.fields['zone_id'] = {'name':'Zone ID', 'visible':['list', 'add', 'update']}


	@cherrypy.expose
	def index(self, flash_message=None):
		tmpl = self.lookup.get_template("sensors.mako")
		return tmpl.render(page_title="Sensors", flash_message=flash_message)






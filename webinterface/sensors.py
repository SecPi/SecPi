import os

# web framework
import cherrypy
import urllib

# db connection
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.types import String, Integer

# web <--> db
from cp_sqlalchemy import SQLAlchemyTool, SQLAlchemyPlugin

# templating engine
from mako.template import Template
from mako.lookup import TemplateLookup

# our stuff
from tools.db import objects
from tools import config
from collections import OrderedDict


lookup = TemplateLookup(directories=['templates'], strict_undefined=True)

class SensorsPage(object):
	
	@property
	def db(self):
		return cherrypy.request.db
	
	@cherrypy.expose
	def index(self, flash_message=None):
		tmpl = lookup.get_template("sensors.mako")
		return tmpl.render(page_title="Sensors", flash_message=flash_message)
		
	@cherrypy.expose
	def list(self, flash_message=None):
		tmpl = lookup.get_template("list.mako")
		sensors = self.db.query(objects.Sensor).all()
		
		fields = OrderedDict()
		fields['id'] = 'ID'
		fields['name'] = 'Name'
		fields['description'] = 'Description'
		fields['gpio_pin'] = 'GPIO Pin'
		fields['zone_id'] = 'Zone ID'
		
		return tmpl.render(data=sensors, page_title="Sensors List", flash_message=flash_message, fields=fields)
		
	@cherrypy.expose
	def delete(self, flash_message, id):
		if id:
			sens = self.db.query(objects.Sensor).get(id)
			if(sens):
				self.db.delete(sens)
				self.db.commit()
			else:
				raise cherrypy.HTTPRedirect("list?%s"% urllib.urlencode({'flash_message': 'ID not found!'}))
				
			
		raise cherrypy.HTTPRedirect("list?%s"%urllib.urlencode({'flash_message': 'Sensor deleted!'}))
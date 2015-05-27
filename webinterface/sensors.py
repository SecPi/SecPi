import os

# web framework
import cherrypy

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

lookup = TemplateLookup(directories=['templates'], strict_undefined=True)

class SensorsPage(object):
	
	@property
	def db(self):
		return cherrypy.request.db
	
	@cherrypy.expose
	def index(self):
		tmpl = lookup.get_template("sensors.mako")
		return tmpl.render(page_title="Sensors")
		
	@cherrypy.expose
	def list(self):
		tmpl = lookup.get_template("list.mako")
		
		sensors = self.db.query(objects.Sensor).all()
		
		
		return tmpl.render(data=sensors, page_title="Sensors List")
		
	@cherrypy.expose
	def delete(self, id):
		if id:
			sens = self.db.query(objects.Sensor).get(id)
			self.db.delete(sens)
			self.db.commit()
		
		raise cherrypy.InternalRedirect("list")
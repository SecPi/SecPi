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
from base_webpage import BaseWebPage



class SensorsPage(BaseWebPage):
	
	def __init__(self):
		super(SensorsPage, self).__init__(objects.Sensor)
		self.fields['id'] = 'ID'
		self.fields['name'] = 'Name'
		self.fields['description'] = 'Description'
		self.fields['gpio_pin'] = 'GPIO Pin'
		self.fields['zone_id'] = 'Zone ID'


	@cherrypy.expose
	def index(self, flash_message=None):
		tmpl = self.lookup.get_template("sensors.mako")
		return tmpl.render(page_title="Sensors", flash_message=flash_message)



		



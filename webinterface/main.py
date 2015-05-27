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

from sensors import SensorsPage


lookup = TemplateLookup(directories=['templates'], strict_undefined=True)

class Root(object):

	def __init__(self):
		self.sensors = SensorsPage()
	
	@property
	def db(self):
		return cherrypy.request.db


	@cherrypy.expose
	def index(self):
		tmpl = lookup.get_template("index.mako")
		return tmpl.render(page_title="Welcome")


def run():
	cherrypy.tools.db = SQLAlchemyTool()

	app_config = {
		'/': {
			'tools.db.on': True,
			'tools.staticdir.root': os.path.join(config.get("project_path"), "webinterface")
		},
		'/static': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': 'static'
		}
	}
	cherrypy.tree.mount(Root(), '/', app_config)
	dbfile = "%s/data.db"%config.get("project_path")

	if not os.path.exists(dbfile):
		open(dbfile, 'w+').close()

	sqlalchemy_plugin = SQLAlchemyPlugin(
		cherrypy.engine, objects.Base, 'sqlite:///%s' % (dbfile),
		echo=True
	)
	sqlalchemy_plugin.subscribe()
	sqlalchemy_plugin.create()
	cherrypy.engine.start()
	cherrypy.engine.block()


if __name__ == '__main__':
	run()
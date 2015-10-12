import os
import json

# web framework
import cherrypy
from cherrypy.lib import auth_digest

# db connection
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.types import String, Integer

# web <--> db
from cp_sqlalchemy import SQLAlchemyTool, SQLAlchemyPlugin

# templating engine
from mako.template import Template
from mako.lookup import TemplateLookup

# rabbitmq
import pika

# our stuff
from tools.db import objects
from tools import config
from tools import utils

# sub pages
from sites.sensors import SensorsPage
from sites.zones import ZonesPage
from sites.setups import SetupsPage
from sites.alarms import AlarmsPage
from sites.workers import WorkersPage
from sites.actions import ActionsPage
from sites.notifiers import NotifiersPage
from sites.params import ParamsPage
from sites.logs import LogEntriesPage

lookup = TemplateLookup(directories=['templates'], strict_undefined=True)
config.load("webinterface")

class Root(object):

	def __init__(self):
		self.sensors = SensorsPage()
		self.zones = ZonesPage()
		self.setups = SetupsPage()
		self.alarms = AlarmsPage()
		self.workers = WorkersPage()
		self.actions = ActionsPage()
		self.notifiers = NotifiersPage()
		self.params = ParamsPage()
		self.logs = LogEntriesPage()
		
		credentials = pika.PlainCredentials(config.get('rabbitmq')['user'], config.get('rabbitmq')['password'])
		parameters = pika.ConnectionParameters(credentials=credentials,
			host=config.get('rabbitmq')['master_ip'],
			port=5671,
			ssl=True,
			ssl_options = { "ca_certs":(config.get("project_path"))+config.get('rabbitmq')['cacert'],
				"certfile":config.get("project_path")+config.get('rabbitmq')['certfile'],
				"keyfile":config.get("project_path")+config.get('rabbitmq')['keyfile']
			}
		)
		connection = pika.BlockingConnection(parameters=parameters)
		self.channel = connection.channel()
		self.channel.queue_declare(queue='on_off')
		self.channel.queue_bind(exchange='manager', queue='on_off')
		
	
	@property
	def db(self):
		return cherrypy.request.db
	

	@cherrypy.expose
	def index(self):
		tmpl = lookup.get_template("index.mako")
		return tmpl.render(page_title="Welcome")
	
	
	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def activate(self):
		if(hasattr(cherrypy.request, 'json')):
			id = cherrypy.request.json['id']
			
			if(id and id > 0):
				su = self.db.query(objects.Setup).get(int(id))
				su.active_state = True
				self.db.commit()
				ooff = { 'active_state': True }
				self.channel.basic_publish(exchange='manager', routing_key='on_off', body=json.dumps(ooff))
				
				return {'status': 'success', 'message': "Activated setup %s!"%su.name}
			
			return {'status':'error', 'message': "Invalid ID!" }
		
		return {'status': 'error', 'message': 'No data recieved!'}
	
	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def deactivate(self):
		if(hasattr(cherrypy.request, 'json')):
			id = cherrypy.request.json['id']
			
			if(id and id > 0):
				su = self.db.query(objects.Setup).get(int(id))
				su.active_state = False
				self.db.commit()
				ooff = { 'active_state': False }
				self.channel.basic_publish(exchange='manager', routing_key='on_off', body=json.dumps(ooff))
				
				return {'status': 'success', 'message': "Deactivated setup %s!"%su.name}
			
			return {'status':'error', 'message': "Invalid ID!" }
		
		return {'status': 'error', 'message': 'No data recieved!'}


def run():
	cherrypy.tools.db = SQLAlchemyTool()
	
	
	cherrypy.config.update({
		'server.socket_host': '0.0.0.0',
		'server.socket_port': 8080,
		'log.error_file': "../logs/webui.log",
		'log.access_file': "../logs/webui_access.log",
		'log.screen': True
	})
	
	app_config = {
		'/': {
			'tools.db.on': True,
			'tools.staticdir.root': os.path.join(config.get("project_path"), "webinterface"),
			'tools.auth_digest.on': True,
	        'tools.auth_digest.realm': 'secpi',
	        'tools.auth_digest.get_ha1': auth_digest.get_ha1_file_htdigest('.htdigest'),
	        'tools.auth_digest.key': 'ae41349f9413b13c'
		},
		'/static': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': 'static'
		},
		 "/favicon.ico":
        {
          "tools.staticfile.on": True,
          "tools.staticfile.filename": config.get("project_path")+"/webinterface/favicon.ico"
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
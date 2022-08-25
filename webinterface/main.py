#!/usr/bin/env python

import sys

if(len(sys.argv)>1):
	PROJECT_PATH = sys.argv[1]
	sys.path.append(PROJECT_PATH)
else:
	print("Error initializing Webinterface, no path given!");
	sys.exit(1)

import os
import json
import traceback
import logging
import logging.config
import subprocess
import time


# web framework
import cherrypy
from cherrypy.lib import auth_digest
from cherrypy import _cperror

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

from mako_template_tool import MakoTemplateTool

# sub pages
from sites.sensors import SensorsPage
from sites.zones import ZonesPage
from sites.setups import SetupsPage
from sites.alarms import AlarmsPage
from sites.workers import WorkersPage
from sites.actions import ActionsPage
from sites.notifiers import NotifiersPage
from sites.actionparams import ActionParamsPage
from sites.notifierparams import NotifierParamsPage
from sites.sensorparams import SensorParamsPage
from sites.logs import LogEntriesPage
from sites.setupszones import SetupsZonesPage
from sites.workersactions import WorkersActionsPage

from sites.alarmdata import AlarmDataPage


try:
	config.load(PROJECT_PATH + "/webinterface/config.json")
except Exception:
	logging.exception("Wasn't able to load config file, exiting...")
	quit()


class Root(object):

	def __init__(self):
		cherrypy.log("Initializing Webserver")
		
		cherrypy.config.update({'request.error_response': self.handle_error})
		cherrypy.config.update({'error_page.404': self.error_404})
		cherrypy.config.update({'error_page.401': self.error_401})
		
		self.sensors = SensorsPage()
		self.zones = ZonesPage()
		self.setups = SetupsPage()
		self.alarms = AlarmsPage()
		self.workers = WorkersPage()
		self.actions = ActionsPage()
		self.notifiers = NotifiersPage()
		self.sensorparams = SensorParamsPage()
		self.actionparams = ActionParamsPage()
		self.notifierparams = NotifierParamsPage()
		self.logs = LogEntriesPage()
		self.setupszones = SetupsZonesPage()
		self.workersactions = WorkersActionsPage()
		
		self.alarmdata = AlarmDataPage()
		
		self.connect()
		cherrypy.log("Finished initialization")
			
	def connect(self, num_tries=3):
		credentials = pika.PlainCredentials(config.get('rabbitmq')['user'], config.get('rabbitmq')['password'])
		parameters = pika.ConnectionParameters(credentials=credentials,
			host=config.get('rabbitmq', {}).get('master_ip', 'localhost'),
			port=int(config.get('rabbitmq', {}).get('master_port', 5672)),
			socket_timeout=10,
			# ssl=True,
			# ssl_options = {
			# 	"ca_certs":PROJECT_PATH+"/certs/"+config.get('rabbitmq')['cacert'],
			# 	"certfile":PROJECT_PATH+"/certs/"+config.get('rabbitmq')['certfile'],
			# 	"keyfile":PROJECT_PATH+"/certs/"+config.get('rabbitmq')['keyfile']
			# }
		)

		connected = False
		while not connected and num_tries > 0:
			try:
				cherrypy.log("Trying to connect to rabbitmq service...")
				self.connection = pika.BlockingConnection(parameters=parameters)
				self.channel = self.connection.channel()
				connected = True
				cherrypy.log("Connection to rabbitmq service established")
				break
			except pika.exceptions.AMQPConnectionError as pe:
				if "The AMQP connection was closed" in repr(pe):
					cherrypy.log("Wasn't able to connect to the rabbitmq service, please check if the rabbitmq service is reachable and running")
				else:
					cherrypy.log("Wasn't able to connect to the rabbitmq service: %s" % repr(pe))
			except Exception as e:
				cherrypy.log("Unknown error: %s" % e)
			
			num_tries-=1
			if(num_tries!=0):
				time.sleep(30)

		if not connected:
			cherrypy.log("Wasn't able to connect to rabbitmq service, exiting...")
			return False
		# define exchange
		self.channel.exchange_declare(exchange=utils.EXCHANGE, exchange_type='direct')

		# define queues
		self.channel.queue_declare(queue=utils.QUEUE_ON_OFF)
		self.channel.queue_bind(queue=utils.QUEUE_ON_OFF, exchange=utils.EXCHANGE)
		return True

	def connection_cleanup(self):
		try:
			self.channel.close()
			self.connection.close()
		except pika.exceptions.ConnectionClosed:
			cherrypy.log("Wasn't able to cleanup connection")

	def log_msg(self, msg, level):
		log_entry = self.db.objects.LogEntry(level=level, message=str(msg), sender="Webinterface")
		self.db.add(log_entry)
		self.db.commit()
	
	@property
	def db(self):
		return cherrypy.request.db
		
	@property
	def lookup(self):
		return cherrypy.request.lookup
	
	def handle_error(self):
		if 'Content-Type' in cherrypy.request.headers and 'application/json' in cherrypy.request.headers['Content-Type'].lower():
			exc_type, exc_value, exc_traceback = sys.exc_info()
			payload = json.dumps({
				"status": 'error',
				"message": f"An exception occurred during processing: {exc_value}",
				"traceback": traceback.format_exc()
			})
			cherrypy.response.status = 200
			cherrypy.response.body = payload.encode("utf-8")
		else:
			tmpl = self.lookup.get_template("500.mako")
			payload = tmpl.render(page_title="Error!", traceback=traceback.format_exc())
			cherrypy.response.status = 500
			cherrypy.response.headers['Content-Type'] = "text/html"
			cherrypy.response.body = payload.encode("utf-8")

	def error_404(self, status, message, traceback, version):
		tmpl = self.lookup.get_template("404.mako")
		cherrypy.response.status = 404
		return tmpl.render(page_title="File not found!")

	def error_401(self, status, message, traceback, version):
		tmpl = self.lookup.get_template("401.mako")
		cherrypy.response.status = 401
		return tmpl.render(page_title="Not Authorized!")

	@cherrypy.expose
	def index(self):
		tmpl = self.lookup.get_template("index.mako")
		return tmpl.render(page_title="Welcome")
	
	@cherrypy.expose
	def test(self):
		tmpl = self.lookup.get_template("test.mako")
		return tmpl.render(page_title="Testing")
	
	@cherrypy.expose
	def change_credentials(self):
		tmpl = self.lookup.get_template("change_credentials.mako")
		return tmpl.render(page_title="Change Login Credentials")

	@cherrypy.expose
	@cherrypy.tools.json_in()
	#@cherrypy.tools.json_out(handler=utils.json_handler)
	def activate(self, **kwargs):
		retval = {}
		is_json = False
		id=0
		
		if(hasattr(cherrypy.request, 'json')):	
			id = cherrypy.request.json['id']
			is_json = True
		elif('id' in kwargs):
			id = kwargs['id']
		else:
			retval = {'status': 'error', 'message': 'No data recieved!'}
			
		if(id and id > 0):
			su = self.db.query(objects.Setup).get(int(id))
			try:
				if(hasattr(self, "channel")):
					su.active_state = True
					self.db.commit()
					ooff = { 'active_state': True , 'setup_name': su.name }
					self.channel.basic_publish(exchange=utils.EXCHANGE, routing_key=utils.QUEUE_ON_OFF, body=json.dumps(ooff))
					retval = {'status': 'success', 'message': "Activated setup %s!" % su.name}
				else:
					retval = {'status':'error', 'message': "Error activating %s! No connection to queue server!" % su.name }
			
			except pika.exceptions.ConnectionClosed:
				cherrypy.log("Reconnecting to RabbitMQ Server!")
				reconnected = self.connect()
				if reconnected:
					cherrypy.log("Reconnect finished!")
					su.active_state = True
					self.db.commit()
					ooff = { 'active_state': True, 'setup_name': su.name }
					self.channel.basic_publish(exchange=utils.EXCHANGE, routing_key=utils.QUEUE_ON_OFF, body=json.dumps(ooff))
					retval = {'status': 'success', 'message': "Activated setup %s!" % su.name}
				else:
					retval = {'status':'error', 'message': "Error activating %s! Wasn't able to reconnect!" % su.name }

			except Exception as e:
				su.active_state = False
				self.db.commit()
				cherrypy.log("Error activating! %s"%str(e), traceback=True)
				retval = {'status':'error', 'message': "Error activating! %s" % e }
				
		else:
			retval = {'status':'error', 'message': "Invalid ID!" }
		
		if(is_json):
			cherrypy.response.headers['Content-Type'] = "application/json"
			return json.dumps(retval)
		else:
			tmpl = self.lookup.get_template("activate.mako")
			return tmpl.render(page_title="Activate", message = retval['message'], status=retval['status'])
		
	@cherrypy.expose
	@cherrypy.tools.json_in()
	#@cherrypy.tools.json_out(handler=utils.json_handler)
	def deactivate(self, **kwargs):
		retval = {}
		is_json = False
		id=0
		
		if(hasattr(cherrypy.request, 'json')):	
			id = cherrypy.request.json['id']
			is_json = True
		elif('id' in kwargs):
			id = kwargs['id']
		else:
			retval = {'status': 'error', 'message': 'No data recieved!'}
			
		if(id and id > 0):
			su = self.db.query(objects.Setup).get(int(id))
			try:
				if(hasattr(self, "channel")):
					su.active_state = False
					self.db.commit()
					ooff = { 'active_state': False , 'setup_name': su.name }
					self.channel.basic_publish(exchange=utils.EXCHANGE, routing_key=utils.QUEUE_ON_OFF, body=json.dumps(ooff))
					retval = {'status': 'success', 'message': "Deactivated setup %s!" % su.name}
				else:
					retval = {'status':'error', 'message': "Error deactivating %s! No connection to queue server!" % su.name }
			
			except pika.exceptions.ConnectionClosed:
				cherrypy.log("Reconnecting to RabbitMQ Server!")
				reconnected = self.connect()
				if reconnected:
					cherrypy.log("Reconnect finished!")
					su.active_state = False
					self.db.commit()
					ooff = { 'active_state': False, 'setup_name': su.name }
					self.channel.basic_publish(exchange=utils.EXCHANGE, routing_key=utils.QUEUE_ON_OFF, body=json.dumps(ooff))
					retval = {'status': 'success', 'message': "Deactivated setup %s!" % su.name}
				else:
					retval = {'status':'error', 'message': "Error deactivating %s! Wasn't able to reconnect!" % su.name }

			except Exception as e:
				su.active_state = True
				self.db.commit()
				cherrypy.log("Error deactivating! %s"%str(e), traceback=True)
				retval = {'status':'error', 'message': "Error deactivating! %s" % e }
				
		else:
			retval = {'status':'error', 'message': "Invalid ID!" }
		
		if(is_json):
			cherrypy.response.headers['Content-Type'] = "application/json"
			return json.dumps(retval)
		else:
			tmpl = self.lookup.get_template("activate.mako")
			return tmpl.render(page_title="Deactivate", message = retval['message'], status=retval['status'])
	
	

	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def change_login(self):
		if(hasattr(cherrypy.request, 'json')):
			username = cherrypy.request.json['username']
			password = cherrypy.request.json['password']
			try:
				exit_code = subprocess.call(["/opt/secpi/webinterface/create_htdigest.sh", PROJECT_PATH+"/webinterface/.htdigest", username, password])
				if not exit_code: # successful
					return {'status': 'success', 'message': "Login credentials have been changed!"}
				else: # exit_code != 0
					return {'status':'error', 'message': "Error changing login credentials!"}
			except Exception as e:
				return {'status':'error', 'message': "Error changing login credentials: %s" % e }


def run():
	# db_log_file_name = '/var/log/secpi/db.log'
	
	# db_handler = logging.FileHandler(db_log_file_name)
	# db_handler.setLevel(logging.WARN)

	db_logger = logging.getLogger('sqlalchemy')
	# db_logger.addHandler(db_handler)
	db_logger.setLevel(logging.WARN)
	
	cherrypy.tools.db = SQLAlchemyTool()
	cherrypy.tools.lookup = MakoTemplateTool('%s/webinterface/templates'%(PROJECT_PATH))
	
	
	cherrypy.config.update({
		'server.socket_host': '0.0.0.0',
		'server.socket_port': 8000,
		# 'server.ssl_module':'pyopenssl',
		# 'server.ssl_certificate':'%s/certs/%s'%(PROJECT_PATH, config.get("server_cert")),
		# 'server.ssl_private_key':'%s/certs/%s'%(PROJECT_PATH, config.get("server_key")),
		# 'server.ssl_certificate_chain':'%s/certs/%s'%(PROJECT_PATH, config.get("server_ca_chain")),
		# 'log.error_file': "/var/log/secpi/webinterface.log",
		# 'log.access_file': "/var/log/secpi/webinterface_access.log",
		'log.screen': True,
		'tools.encode.on': True,
		'tools.encode.encoding': 'utf-8',
		'tools.encode.text_only': False,
	})
	
	app_config = {
		'/': {
			'tools.db.on': True,
			'tools.lookup.on': True,
			'tools.staticdir.root': os.path.join(PROJECT_PATH, "webinterface"),
			'tools.auth_digest.on': False,
			'tools.auth_digest.realm': 'secpi',
			'tools.auth_digest.get_ha1': auth_digest.get_ha1_file_htdigest('%s/webinterface/.htdigest'%(PROJECT_PATH)),
			'tools.auth_digest.key': 'ae41349f9413b13c'
		},
		'/static': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': 'static'
		},
		 "/favicon.ico":
		{
		  "tools.staticfile.on": True,
		  "tools.staticfile.filename": PROJECT_PATH+"/webinterface/favicon.ico"
		}
	}
	cherrypy.tree.mount(Root(), '/', app_config)
	dbfile = "%s/data.db"%PROJECT_PATH

	if not os.path.exists(dbfile):
		open(dbfile, 'w+').close()

	sqlalchemy_plugin = SQLAlchemyPlugin(
		cherrypy.engine, objects.Base, 'sqlite:///%s' % (dbfile),
		echo=False
	)
	sqlalchemy_plugin.subscribe()
	sqlalchemy_plugin.create()

	cherrypy.engine.start()
	cherrypy.engine.block()


if __name__ == '__main__':
	run()

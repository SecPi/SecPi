import dataclasses
import json
import logging
import os
import subprocess
import sys
import traceback

import cherrypy
import pika
import pkg_resources
from cherrypy.lib import auth_digest
from cp_sqlalchemy import SQLAlchemyPlugin, SQLAlchemyTool
from tools import utils
from tools.amqp import AMQPAdapter
from tools.cli import StartupOptions, parse_cmd_args
from tools.config import ApplicationConfig
from tools.db.objects import Base, LogEntry, Setup
from tools.utils import setup_logging

from .mako_template_tool import MakoTemplateTool
from .sites.actionparams import ActionParamsPage
from .sites.actions import ActionsPage
from .sites.alarmdata import AlarmDataPage
from .sites.alarms import AlarmsPage
from .sites.logs import LogEntriesPage
from .sites.notifierparams import NotifierParamsPage
from .sites.notifiers import NotifiersPage
from .sites.sensorparams import SensorParamsPage
from .sites.sensors import SensorsPage
from .sites.setups import SetupsPage
from .sites.setupszones import SetupsZonesPage
from .sites.workers import WorkersPage
from .sites.workersactions import WorkersActionsPage
from .sites.zones import ZonesPage

logger = logging.getLogger(__name__)


sqlalchemy_plugin = None


@dataclasses.dataclass
class ActivationRequest:
	"""
	Carry information about a setup activation request.
	"""
	setup_identifier: int = None
	is_json: bool = False


@dataclasses.dataclass
class ActivationResponse:
	"""
	Carry information about a setup activation response.
	"""
	message: str = None

	@property
	def status(self):
		if self.error:
			return "error"
		else:
			return "success"

	def to_dict(self):
		return {
			"status": self.status,
			"message": self.message,
		}


class SuccessfulResponse(ActivationResponse):
	"""
	Message for a successful operation.
	"""
	error = False


class FailedResponse(ActivationResponse):
	"""
	Message for a failed operation.
	"""
	error = True


class Webinterface:
	"""
	The SecPi web interface.
	"""

	def __init__(self, config: ApplicationConfig):

		logger.info("Initializing Webserver")

		self.config = config
		self.is_shutting_down = False

		cherrypy.config.update({'request.error_response': self.handle_error})
		# cherrypy.config.update({'error_page.default': self.jsonify_error})
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
		
		# Connect to messaging bus.
		self.channel: pika.channel.Channel = None
		self.bus = AMQPAdapter(
			hostname=config.get('rabbitmq', {}).get('master_ip', 'localhost'),
			port=int(config.get('rabbitmq', {}).get('master_port', 5672)),
			username=config.get('rabbitmq')['user'],
			password=config.get('rabbitmq')['password'],
		)
		self.connect()

		logger.info("Finished initialization")
			
	def connect(self):
		self.bus.connect()
		self.channel = self.bus.channel

		if self.bus.available:
			logger.info("AMQP: Connected to broker")
		else:
			logger.error("AMQP: No connection to broker")
			return False

		# Define exchange.
		self.channel.exchange_declare(exchange=utils.EXCHANGE, exchange_type='direct')

		# Define queues.
		self.channel.queue_declare(queue=utils.QUEUE_ON_OFF)
		self.channel.queue_bind(exchange=utils.EXCHANGE, queue=utils.QUEUE_ON_OFF)
		return True

	def connection_cleanup(self):
		try:
			self.bus.disconnect()
		except pika.exceptions.ConnectionClosed:
			logger.warning("Wasn't able to cleanup connection")

	def log_msg(self, msg, level):
		log_entry = LogEntry(level=level, message=str(msg), sender="Webinterface")
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
			payload = tmpl.render(page_title="Error", traceback=traceback.format_exc())
			cherrypy.response.status = 500
			cherrypy.response.headers['Content-Type'] = "text/html"
			cherrypy.response.body = payload.encode("utf-8")

	def error_404(self, status, message, traceback, version):
		tmpl = self.lookup.get_template("404.mako")
		cherrypy.response.status = 404
		return tmpl.render(page_title="File not found")

	def error_401(self, status, message, traceback, version):
		tmpl = self.lookup.get_template("401.mako")
		cherrypy.response.status = 401
		return tmpl.render(page_title="Not Authorized")

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

		# Read activation request.
		request = self.read_activation_request(**kwargs)
		logger.info(f"Activating setup id={request.setup_identifier}")

		# Process activation.
		if request.setup_identifier is not None:
			response = self.toggle_activation(request, active=True)
		else:
			response = FailedResponse("Invalid ID, or no data received")
		
		# Render response.
		return self.render_activation_response(request=request, response=response, page_title="Activate")

	@cherrypy.expose
	@cherrypy.tools.json_in()
	#@cherrypy.tools.json_out(handler=utils.json_handler)
	def deactivate(self, **kwargs):

		# Read activation request.
		request = self.read_activation_request(**kwargs)
		logger.info(f"Deactivating setup id={request.setup_identifier}")

		# Process activation.
		if request.setup_identifier is not None:
			response = self.toggle_activation(request, active=False)
		else:
			response = FailedResponse("Invalid ID, or no data received")

		# Render response.
		return self.render_activation_response(request=request, response=response, page_title="Deactivate")

	def read_activation_request(self, **kwargs):
		"""
		Read "setup identifier" from HTTP request.
		"""
		is_json = False

		setup_id = None
		if hasattr(cherrypy.request, 'json'):
			setup_id = cherrypy.request.json['id']
			is_json = True
		elif 'id' in kwargs:
			setup_id = kwargs['id']

		if setup_id is not None:
			setup_id = int(setup_id)

		return ActivationRequest(setup_identifier=setup_id, is_json=is_json)

	def toggle_activation(self, request: ActivationRequest, active: bool):
		"""
		Activate or deactivate a setup.
		"""

		verb = "activating"
		if not active:
			verb = "deactivating"

		if request.setup_identifier is None:
			return FailedResponse("Invalid setup identifier, or no data received")

		setup = self.db.query(Setup).get(request.setup_identifier)

		if not self.bus.available:
			return FailedResponse(f"Error {verb} setup '{setup.name}', not connected to bus")

		setup.active_state = active
		self.db.commit()

		message = {"setup_name": setup.name, "active_state": active}
		try:
			self.publish(queue=utils.QUEUE_ON_OFF, message=message)
			response = SuccessfulResponse(f"{verb.title()} setup '{setup.name}' succeeded")

		except pika.exceptions.ConnectionClosed:
			logger.info("Reconnecting to RabbitMQ Server")
			reconnected = self.connect()
			if reconnected:
				logger.info("Reconnect finished")
				self.publish(queue=utils.QUEUE_ON_OFF, message=message)
				response = SuccessfulResponse(f"{verb.title()} setup '{setup.name}' succeeded")
			else:
				response = FailedResponse(f"Error {verb} setup '{setup.name}', not connected to bus")

		except Exception as ex:
			message = f"Error {verb} setup '{setup.name}'"
			logger.exception(message)
			response = FailedResponse(f"{message}: {ex}")

		if isinstance(response, SuccessfulResponse):
			logger.info(f"Action successful: {response}")
		else:
			logger.error(f"Action failed: {response}")
		return response

	def publish(self, queue, message):
		"""
		Publish message to the AMQP bus.
		"""
		logger.info(f"Publishing message. queue={queue}, message={message}")
		message = json.dumps(message)
		data = dict(exchange=utils.EXCHANGE, routing_key=queue, body=message)
		return self.channel.basic_publish(**data)

	def render_activation_response(self, request: ActivationRequest, response: ActivationResponse, **kwargs):
		"""
		Render an HTTP response for the setup activation/deactivation.
		"""
		data = response.to_dict()
		data.update(kwargs)
		if request.is_json:
			cherrypy.response.headers['Content-Type'] = "application/json"
			return json.dumps(data)
		else:
			tmpl = self.lookup.get_template("activate.mako")
			return tmpl.render(data)

	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def change_login(self):
		"""
		Change login credentials.

		TODO: Review and eventually rip it out completely.
		"""
		if hasattr(cherrypy.request, 'json'):
			username = cherrypy.request.json['username']
			password = cherrypy.request.json['password']
			try:
				# FIXME: Get rid of hardcoded details.
				exit_code = subprocess.call(["/opt/secpi/webinterface/create_htdigest.sh", PROJECT_PATH+"/webinterface/.htdigest", username, password])
				if exit_code == 0:
					return SuccessfulResponse("Login credentials have been changed").to_dict()
				else:
					return FailedResponse("Error changing login credentials").to_dict()
			except Exception as ex:
				message = f"Error changing login credentials: {ex}"
				logger.exception(message)
				return FailedResponse(message).to_dict()

	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def operational(self):
		"""
		HTTP: Receive and process operational messages.

		Currently, this implements the handler for the shutdown signal, which is mostly
		needed in testing scenarios.

		Usage::

		    echo '{"action": "shutdown"}' | http POST http://localhost:8000/operational
		"""
		message = cherrypy.request.json
		logger.info(f"Got message on operational endpoint: {message}")
		try:
			action = message.get("action")

			# Invoke shutdown.
			if action == "shutdown":
				if True or "PYTEST_CURRENT_TEST" in os.environ:
					self.stop()
					return SuccessfulResponse("Shutdown accepted").to_dict()
				else:
					message = "Remote shutdown not allowed, skipping signal"
					logger.warning(message)
					return FailedResponse(message).to_dict()
		except:
			if self.is_shutting_down:
				raise SystemExit(0)
			logger.exception("Processing operational message failed")
			raise

	def stop(self):
		"""
		Stop the service.
		"""
		logger.info("Shutting down")

		self.bus.unsubscribe()
		self.bus.disconnect()

		self.is_shutting_down = True
		sys.exit(1)

	'''
	def jsonify_error(self, status, message, traceback, version):
		"""
		Make CherryPy return errors in JSON format.

		https://stackoverflow.com/a/58099906
		"""
		response = cherrypy.response
		response.headers['Content-Type'] = 'application/json'
		return json.dumps(dict(
			status="error",
			message=status,
			description=message,
		), indent=2)
	'''


def run_webinterface(options: StartupOptions):

	logger.info("Configuring Webinterface")

	cherrypy.tools.db = SQLAlchemyTool()

	# TODO: Review those locations.
	root_path = pkg_resources.resource_filename(__name__, "")
	favicon_path = pkg_resources.resource_filename(__name__, "favicon.ico")
	htdigest_path = pkg_resources.resource_filename(__name__, ".htdigest")
	template_path = pkg_resources.resource_filename(__name__, "templates")

	cherrypy.tools.lookup = MakoTemplateTool(template_path)
	logger.info(f"Using template path {template_path}")

	cherrypy.config.update({
		'server.socket_host': '0.0.0.0',
		'server.socket_port': 8000,
		# 'server.ssl_module':'pyopenssl',
		# 'server.ssl_certificate':'%s/certs/%s'%(PROJECT_PATH, config.get("webserver", {}).get("server_cert")),
		# 'server.ssl_private_key':'%s/certs/%s'%(PROJECT_PATH, config.get("webserver", {}).get("server_key")),
		# 'server.ssl_certificate_chain':'%s/certs/%s'%(PROJECT_PATH, config.get("webserver", {}).get("server_ca_chain")),
		# 'log.error_file': "/var/log/secpi/webinterface.log",
		# 'log.access_file': "/var/log/secpi/webinterface_access.log",
		'log.screen': False,
		'tools.encode.on': True,
		'tools.encode.encoding': 'utf-8',
		'tools.encode.text_only': False,
	})

	cherrypy_app_config = {
		'/': {
			'tools.db.on': True,
			'tools.lookup.on': True,
			'tools.staticdir.root': root_path,
			'tools.auth_digest.on': False,
			'tools.auth_digest.realm': 'secpi',
			'tools.auth_digest.get_ha1': auth_digest.get_ha1_file_htdigest(htdigest_path),
			'tools.auth_digest.key': 'ae41349f9413b13c'
		},
		'/static': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': 'static'
		},
		"/favicon.ico": {
			"tools.staticfile.on": True,
			"tools.staticfile.filename": favicon_path,
		}
	}

	# Read configuration from file.
	try:
		app_config = ApplicationConfig(filepath=options.app_config)
		app_config.load()
	except:
		logger.exception("Loading configuration failed")
		sys.exit(1)

	# Connect to database.
	database_uri = app_config.get("database", {}).get("uri")
	if database_uri is None:
		raise ConnectionError(f"Unable to connect to database. Database URI is: {database_uri}")
	logger.info(f"Connecting to database {database_uri}")
	global sqlalchemy_plugin
	sqlalchemy_plugin = SQLAlchemyPlugin(
		cherrypy.engine, Base, database_uri,
		echo=False
	)
	sqlalchemy_plugin.subscribe()
	sqlalchemy_plugin.create()
	# Create web application object.
	app = Webinterface(config=app_config)

	# TODO: Configure development vs. production.
	cherrypy.config.update({
		"global": {
			# "environment": "production",
		}
	})
	cherrypy.tree.mount(app, '/', config=cherrypy_app_config)

	# Start CherryPy.
	cherrypy.engine.start()
	cherrypy.engine.block()


def main():
	options = parse_cmd_args()
	setup_logging(level=logging.DEBUG, config_file=options.logging_config, log_file=options.log_file)

	# Enable logging for SQLAlchemy.
	# db_logger = logging.getLogger("sqlalchemy")
	# db_logger.setLevel(logging.INFO)

	run_webinterface(options)
	logging.shutdown()


if __name__ == '__main__':
	main()

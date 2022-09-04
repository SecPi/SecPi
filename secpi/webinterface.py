import dataclasses
import json
import logging
import os
import sys
import traceback
import typing as t

import cherrypy
import pika
import pkg_resources
from cp_sqlalchemy import SQLAlchemyPlugin, SQLAlchemyTool

from secpi.model import constants
from secpi.model.dbmodel import Base, LogEntry, Setup
from secpi.model.settings import StartupOptions
from secpi.util.amqp import AMQPAdapter
from secpi.util.cli import parse_cmd_args
from secpi.util.common import setup_logging
from secpi.util.config import ApplicationConfig
from secpi.util.web import json_handler
from secpi.web.mako_template_tool import MakoTemplateTool
from secpi.web.page import (
    ActionParamsPage,
    ActionsPage,
    AlarmDataPage,
    AlarmsPage,
    LogEntriesPage,
    NotifierParamsPage,
    NotifiersPage,
    SensorParamsPage,
    SensorsPage,
    SetupsPage,
    SetupsZonesPage,
    WorkersActionsPage,
    WorkersPage,
    ZonesPage,
)

logger = logging.getLogger(__name__)


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

        cherrypy.config.update({"request.error_response": self.handle_error})
        # cherrypy.config.update({'error_page.default': self.jsonify_error})
        cherrypy.config.update({"error_page.404": self.error_404})
        cherrypy.config.update({"error_page.401": self.error_401})

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

        # Set up SQLAlchemy and CherryPy.
        self.setup()

        # Connect to messaging bus.
        self.bus = AMQPAdapter.from_uri(config.get("amqp", {}).get("uri"))
        self.connect()

        logger.info("Finished initialization")

    def setup(self):
        logger.info("Configuring Webinterface")

        cherrypy.tools.db = SQLAlchemyTool()

        # TODO: Review those locations.
        static_path = pkg_resources.resource_filename("secpi.web", "static")
        templates_path = pkg_resources.resource_filename("secpi.web", "templates")
        favicon_path = pkg_resources.resource_filename("secpi.web", "favicon.ico")

        cherrypy.tools.lookup = MakoTemplateTool(templates_path)
        logger.info(f"Using template path {templates_path}")

        cherrypy.config.update(
            {
                # TODO: Make configurable.
                "server.socket_host": "0.0.0.0",
                # TODO: Make configurable. Use other non-standard port as default.
                "server.socket_port": 8000,
                # TODO: Make configurable. Would logging to stderr be actually enough?
                # 'log.error_file': "/var/log/secpi/webinterface.log",
                # 'log.access_file': "/var/log/secpi/webinterface_access.log",
                "log.screen": False,
                "tools.encode.on": True,
                "tools.encode.encoding": "utf-8",
                "tools.encode.text_only": False,
            }
        )

        cherrypy_app_config = {
            "/": {
                "tools.db.on": True,
                "tools.lookup.on": True,
            },
            "/static": {
                "tools.staticdir.on": True,
                "tools.staticdir.dir": static_path,
            },
            "/favicon.ico": {
                "tools.staticfile.on": True,
                "tools.staticfile.filename": favicon_path,
            },
        }

        # Connect to database.
        database_uri = self.config.get("database", {}).get("uri")
        if database_uri is None:
            raise ConnectionError(f"Unable to connect to database. Database URI is: {database_uri}")
        logger.info(f"Connecting to database {database_uri}")
        sqlalchemy_plugin = SQLAlchemyPlugin(cherrypy.engine, Base, database_uri, echo=False)
        sqlalchemy_plugin.subscribe()
        sqlalchemy_plugin.create()

        # TODO: Configure development vs. production.
        cherrypy.config.update(
            {
                "global": {
                    "environment": "production",
                }
            }
        )
        cherrypy.tree.mount(self, "/", config=cherrypy_app_config)

    def start(self):
        """
        Start CherryPy.
        """
        cherrypy.engine.start()
        cherrypy.engine.block()

    def connect(self):
        self.bus.connect()

        if self.bus.available:
            logger.info("AMQP: Connected to broker")
        else:
            logger.error("AMQP: No connection to broker")
            return False

        # Define exchange.
        self.bus.channel.exchange_declare(exchange=constants.EXCHANGE, exchange_type="direct")

        # Define queues.
        self.bus.channel.queue_declare(queue=constants.QUEUE_ON_OFF)
        self.bus.channel.queue_bind(queue=constants.QUEUE_ON_OFF, exchange=constants.EXCHANGE)
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
        if (
            "Content-Type" in cherrypy.request.headers
            and "application/json" in cherrypy.request.headers["Content-Type"].lower()
        ):
            exc_type, exc_value, exc_traceback = sys.exc_info()
            payload = json.dumps(
                {
                    "status": "error",
                    "message": f"An exception occurred during processing: {exc_value}",
                    "traceback": traceback.format_exc(),
                }
            )
            cherrypy.response.status = 200
            cherrypy.response.body = payload.encode("utf-8")
        else:
            tmpl = self.lookup.get_template("500.mako")
            payload = tmpl.render(page_title="Error", traceback=traceback.format_exc())
            cherrypy.response.status = 500
            cherrypy.response.headers["Content-Type"] = "text/html"
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
    @cherrypy.tools.json_in()
    # @cherrypy.tools.json_out(handler=json_handler)
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
    # @cherrypy.tools.json_out(handler=json_handler)
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
        if hasattr(cherrypy.request, "json"):
            setup_id = cherrypy.request.json["id"]
            is_json = True
        elif "id" in kwargs:
            setup_id = kwargs["id"]

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

        # TODO: Are we sure that we want/have to use the database here?
        setup.active_state = active
        self.db.commit()

        message = {"setup_name": setup.name, "active_state": active}
        try:
            self.publish(queue=constants.QUEUE_ON_OFF, message=message)
            response = SuccessfulResponse(f"{verb.title()} setup '{setup.name}' succeeded")

        except (pika.exceptions.ConnectionClosed, pika.exceptions.StreamLostError):
            logger.info("Reconnecting to AMQP broker")
            reconnected = self.connect()
            if reconnected:
                logger.info("Reconnect finished")
                self.publish(queue=constants.QUEUE_ON_OFF, message=message)
                response = SuccessfulResponse(f"{verb.title()} setup '{setup.name}' succeeded")
            else:
                response = FailedResponse(f"Error {verb} setup '{setup.name}', not connected to bus")

        except Exception as ex:
            message = f"Error {verb} setup '{setup.name}'"
            logger.exception(message)
            response = FailedResponse(f"{message}: {ex}")

        if isinstance(response, SuccessfulResponse):
            logger.info(f"Activate/deactivate successful: {response}")
        else:
            logger.error(f"Activate/deactivate failed: {response}")
        return response

    def publish(self, queue, message):
        """
        Publish message to the AMQP bus.
        """
        logger.info(f"Publishing message. queue={queue}, message={message}")
        message = json.dumps(message)
        data = dict(exchange=constants.EXCHANGE, routing_key=queue, body=message)
        return self.bus.channel.basic_publish(**data)

    def render_activation_response(self, request: ActivationRequest, response: ActivationResponse, **kwargs):
        """
        Render an HTTP response for the setup activation/deactivation.
        """
        data = response.to_dict()
        data.update(kwargs)
        if request.is_json:
            cherrypy.response.headers["Content-Type"] = "application/json"
            return json.dumps(data)
        else:
            tmpl = self.lookup.get_template("activate.mako")
            return tmpl.render(data)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(handler=json_handler)
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


def run_webinterface(options: StartupOptions):

    # Read configuration from file.
    try:
        app_config = ApplicationConfig(filepath=options.app_config)
        app_config.load()
    except:
        logger.exception("Loading configuration failed")
        sys.exit(1)

    # Create web application object.
    app = Webinterface(config=app_config)
    app.start()


def main(options: t.Optional[StartupOptions] = None):
    if not options:
        options = parse_cmd_args()
    setup_logging(level=logging.DEBUG, config_file=options.logging_config, log_file=options.log_file)

    # Enable logging for SQLAlchemy.
    # db_logger = logging.getLogger("sqlalchemy")
    # db_logger.setLevel(logging.INFO)

    run_webinterface(options)
    logging.shutdown()


if __name__ == "__main__":
    main()

"""
Configuration::

	ID:          1
	Name:        tcp-listener-1234
	Description: Example TCP listener
	Zone ID:     1
	Worker ID:   1
	Class:       TCPPortListener
	Module:      tcpportlistener

Trigger alarm::

	echo hello | socat - tcp:localhost:1234
"""
import logging
import socketserver
import threading

from secpi.model.sensor import Sensor

logger = logging.getLogger(__name__)


class TCPPortListener(Sensor):
    def __init__(self, id, params, worker):
        logger.info(f"Initializing sensor id={id} with parameters {params}")
        super(TCPPortListener, self).__init__(id, params, worker)
        self.active = False
        address = (self.params["ip"], int(self.params["port"]))
        self.server = SecPiTCPServer(self, address, SecPiTCPHandler)
        logger.info("TCPPortListener: Sensor initialized")

    def activate(self):
        self.active = True
        t = threading.Thread(target=self.server.serve_forever)
        t.setDaemon(True)
        t.start()
        self.post_log(f"TCPPortListener: Sensor activated successfully, id={self.id}")

    def deactivate(self):
        self.active = False
        self.server.shutdown()
        self.server.server_close()
        self.post_log(f"TCPPortListener: Sensor deactivated successfully, id={self.id}")


# Request Handler
class SecPiTCPHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)
        return

    def handle(self):
        data = self.request.recv(1024)
        self.request.close()
        return


class SecPiTCPServer(socketserver.TCPServer):

    allow_reuse_address = True

    def __init__(self, sensor, server_address, handler_class=SecPiTCPHandler):
        super(SecPiTCPServer, self).__init__(server_address, handler_class)
        self.sensor = sensor
        return

    def finish_request(self, request, client_address):
        self.sensor.alarm("Got TCP connection, raising alarm")
        return socketserver.TCPServer.finish_request(self, request, client_address)

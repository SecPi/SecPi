import socket
import sys
import SocketServer
import threading
from tools.sensor import Sensor


class TCPPortListener(Sensor):

	def __init__(self, id, params, worker):
		super(TCPPortListener, self).__init__(id, params, worker)
		self.active = False
		address = (self.params["ip"], int(self.params["port"])
		self.server = SecPiTCPServer(address, SecPiTCPHandler)

	def activate(self):
		self.active = True

		t = threading.Thread(target=self.server.serve_forever)
		t.setDaemon(True)
		t.start()

	def deactivate(self):
		self.active = False
		self.server.server_close()

# Request Handler
import SocketServer
class SecPiTCPHandler(SocketServer.BaseRequestHandler):
	
	def __init__(self, request, client_address, server):
		SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
		return

	def setup(self):
		return SocketServer.BaseRequestHandler.setup(self)

	def handle(self):
		# Echo the back to the client
		data = self.request.recv(1024)
		# Call something
		print "GOT STUFF: %s" % data
		return

	def finish(self):
		return SocketServer.BaseRequestHandler.finish(self)

# Server
import SocketServer
class SecPiTCPServer(SocketServer.TCPServer):
	
	def __init__(self, server_address, handler_class=SecPiTCPHandler):
		SocketServer.TCPServer.__init__(self, server_address, handler_class)
		return

	def server_activate(self):
		SocketServer.TCPServer.server_activate(self)
		return

	def serve_forever(self):
		while True:
			self.handle_request()
		return

	def handle_request(self):
		return SocketServer.TCPServer.handle_request(self)

	def verify_request(self, request, client_address):
		return SocketServer.TCPServer.verify_request(self, request, client_address)

	def process_request(self, request, client_address):
		return SocketServer.TCPServer.process_request(self, request, client_address)

	def server_close(self):
		return SocketServer.TCPServer.server_close(self)

	def finish_request(self, request, client_address):
		return SocketServer.TCPServer.finish_request(self, request, client_address)

	def close_request(self, request_address):
		return SocketServer.TCPServer.close_request(self, request_address)


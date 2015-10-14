import socket
import sys
import SocketServer
import threading
from tools.sensor import Sensor

class TCPPortListener(Sensor):

	def __init__(self, id, params, worker):
		super(TCPPortListener, self).__init__(id, params, worker)
		self.active = False
		address = (self.params["ip"], int(self.params["port"]))
		self.server = SocketServer.TCPServer(address, SecPiTCPHandler)

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
	
	def handle(self):
		data = self.request.recv(1024)
		# Call something
		print "GOT STUFF: %s" % data
		self.request.close()
		return

# web framework
import cherrypy
from cherrypy.lib.static import serve_file

from os import walk
from os import listdir
from os import path
import datetime
import math


# our stuff
from tools.db import objects
from tools import config
from tools import utils



class AlarmDataPage():
	
	
	def __init__(self):
		self.datapath = "/var/tmp/secpi/alarms"
		self.suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
		
	@property
	def lookup(self):
		return cherrypy.request.lookup

	@cherrypy.expose
	def index(self):
		tmpl = self.lookup.get_template("alarmdata.mako")
		return tmpl.render(page_title="Alarm Data")

	def get_size(self, start_path):
		total_size = 0
		for dirpath, dirnames, filenames in walk(start_path):
			for f in filenames:
				fp = path.join(dirpath, f)
				total_size += path.getsize(fp)
				
		return total_size


	def human_size(self, nbytes):
		rank = int((math.log10(nbytes)) / 3)
		rank = min(rank, len(self.suffixes) - 1)
		human = nbytes / (1024.0 ** rank)
		f = ('%.2f' % human).rstrip('0').rstrip('.')
		return '%s %s' % (f, self.suffixes[rank])

	
	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def list(self):
		dirs = []
		
		for d in listdir(self.datapath):
			dp = path.join(self.datapath, d)
			if path.isdir(dp):
				dirs.append({
					"name": d,
					"path": dp,
					"mtime": datetime.datetime.fromtimestamp(path.getmtime(dp)).strftime('%d.%m.%Y %H:%M:%S'),
					"size": path.getsize(dp),
					"hsize": self.human_size(self.get_size(dp)),
					"files": listdir(dp)
				})
		
		
		return {'status': 'success', 'data': dirs}

	@cherrypy.expose
	def download(self, name):
		fp = path.join(self.datapath, name)
		if(path.exists(fp)):
			return serve_file(fp, "application/x-download", "attachment")
		else:
			tmpl = self.lookup.get_template("404.mako")
			cherrypy.response.status = 404
			return tmpl.render(page_title="File not found!")


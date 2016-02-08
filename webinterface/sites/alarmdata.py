# web framework
import cherrypy
from cherrypy.lib.static import serve_file

from os import walk
from os import listdir
from os import path
import datetime
import math
import zipfile


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
		# TODO: error management
		for d in listdir(self.datapath):
			dp = path.join(self.datapath, d)
			if path.isdir(dp):
				dirs.append({
					"name": d,
					"path": dp,
					"mtime": datetime.datetime.fromtimestamp(path.getmtime(dp)).strftime('%d.%m.%Y %H:%M:%S')
					# "size": path.getsize(dp),
					# "hsize": self.human_size(self.get_size(dp))
				})
		
		dirs.sort(key=lambda dir: dir['name'], reverse=True)
		
		return {'status': 'success', 'data': dirs}
		
	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def listFiles(self):
		if(hasattr(cherrypy.request, 'json')):
			if('folder' in cherrypy.request.json and cherrypy.request.json['folder']!=''):
				fp = path.join(self.datapath, cherrypy.request.json['folder'])
				try:
					files = [f for f in listdir(fp) if path.isfile(path.join(fp, f))]
					return {'status': 'success', 'data': files}
				except Exception as e:
					return {'status': 'error', 'message': "Couldn't list files! %s"%e}
				
			else:
				return {'status': 'error', 'message': "Invalid folder name!"}
		else:
			return {'status': 'error', 'message': "No folder name given!"}
		
	
	@cherrypy.expose
	def show_img(self, name, mimetype):
		fp = path.join(self.datapath, name)
		if(path.exists(fp)):
			return serve_file(fp, mimetype, name)
		else:
			tmpl = self.lookup.get_template("404.mako")
			cherrypy.response.status = 404
			return tmpl.render(page_title="File not found!")
	

	@cherrypy.expose
	def download(self, name):
		fp = path.join(self.datapath, name)
		if(path.exists(fp)):
			return serve_file(fp, "application/x-download", "attachment")
		else:
			tmpl = self.lookup.get_template("404.mako")
			cherrypy.response.status = 404
			return tmpl.render(page_title="File not found!")


	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def extract(self):
		if(hasattr(cherrypy.request, 'json')):
			if('dir' in cherrypy.request.json and cherrypy.request.json['dir']!='' and 'name' in cherrypy.request.json and cherrypy.request.json['name']!=''):
				dir = cherrypy.request.json['dir']
				name = cherrypy.request.json['name']
				
				fdir = path.join(self.datapath, dir)
				fp = path.join(fdir, name)
				if(path.exists(fp)):
					with zipfile.ZipFile(fp, "r") as z:
						z.extractall(fdir)
						return {'status': 'success', 'message': "File %s/%s extracted!"%(dir, name)}
				else:
					return {'status': 'error', 'message': "File doesn't exist!"}
			else:
				return {'status': 'error', 'message': "Invalid filename!"}
		else:
			return {'status': 'error', 'message': "No filename given!"}
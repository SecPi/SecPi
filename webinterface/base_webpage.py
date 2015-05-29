# web framework
import cherrypy

# templating engine
from mako.lookup import TemplateLookup
from collections import OrderedDict


import urllib

class BaseWebPage(object):
	"""A baseclass for a CherryPy web page."""
	
	def __init__(self, baseclass):
		self.baseclass = baseclass
		self.lookup = TemplateLookup(directories=['templates'], strict_undefined=True)
		self.fields = OrderedDict()
		
	@property
	def db(self):
		return cherrypy.request.db
	
	@cherrypy.expose
	def list(self, flash_message=None):
		tmpl = self.lookup.get_template("list.mako")
		objects = self.db.query(self.baseclass).all()
		
		return tmpl.render(data=objects, page_title="List", flash_message=flash_message, fields=self.fields)
	
	
	@cherrypy.expose
	def delete(self, id):
		if id:
			obj = self.db.query(self.baseclass).get(id)
			if(obj):
				self.db.delete(obj)
				self.db.commit()
			else:
				raise cherrypy.HTTPRedirect("list?%s"% urllib.urlencode({'flash_message': 'ID not found!'}))
				
			
		raise cherrypy.HTTPRedirect("list?%s"%urllib.urlencode({'flash_message': 'Object deleted!'}))
		
		
	@cherrypy.expose
	def add(self, flash_message=None, **params):
		tmpl = self.lookup.get_template("add.mako")
		
		if(params and len(params)>0):
			cherrypy.log("got something %s"%params)
			newObj = self.baseclass(params)
			self.db.add(newObj)
			self.db.commit()
			flash_message="Added new object with id %i"%newObj.id
			
				
		
		return tmpl.render(page_title="Add", flash_message=flash_message, fields=self.fields)







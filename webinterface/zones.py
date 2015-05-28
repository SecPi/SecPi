# web framework
import cherrypy


# our stuff
from tools.db import objects
from tools import config
from base_webpage import BaseWebPage



class ZonesPage(BaseWebPage):
	
	def __init__(self):
		super(ZonesPage, self).__init__(objects.Zone)
		self.fields['id'] = 'ID'
		self.fields['name'] = 'Name'
		self.fields['description'] = 'Description'


	@cherrypy.expose
	def index(self, flash_message=None):
		tmpl = self.lookup.get_template("zones.mako")
		return tmpl.render(page_title="Zones", flash_message=flash_message)






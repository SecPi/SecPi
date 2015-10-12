# web framework
import cherrypy

# our stuff
from tools.db import objects
from tools import config
from tools import utils



class SetupsZonesPage():
	
	#def __init__(self):
		

	@property
	def db(self):
		return cherrypy.request.db

	'''
{
	"setup_id": 1,
	"zone_id": 2	
}
	'''
	@cherrypy.expose()
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def add(self):
		if(hasattr(cherrypy.request, 'json')):
			setup_id = cherrypy.request.json['setup_id']
			zone_id = cherrypy.request.json['zone_id']
			
			if(setup_id and setup_id > 0 and zone_id and zone_id > 0):
				setup = self.db.query(objects.Setup).get(setup_id)
				zone = self.db.query(objects.Zone).get(zone_id)
				
				setup.zones.append(zone)
				self.db.commit()
				return {'status': 'success', 'message': 'Added Zone %s to Setup %s!'%(setup.name, zone.name)}
			
		
		return {'status': 'error', 'message': 'Invalid IDs!'}

	@cherrypy.expose()
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def delete(self):
		if(hasattr(cherrypy.request, 'json')):
			setup_id = cherrypy.request.json['setup_id']
			zone_id = cherrypy.request.json['zone_id']
			
			if(setup_id and setup_id > 0 and zone_id and zone_id > 0):
				setup = self.db.query(objects.Setup).get(setup_id)
				zone = self.db.query(objects.Zone).get(zone_id)
				
				setup.zones.remove(zone)
				self.db.commit()
				return {'status': 'success', 'message': 'Removed Zone %s from Setup %s!'%(setup.name, zone.name)}
			
		
		return {'status': 'error', 'message': 'Invalid IDs!'}


	@cherrypy.expose()
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def list(self):
		setups = self.db.query(objects.Setup).all()
		
		data = []
		
		for su in setups:
			zones = []
			for z in su.zones:
				zones.append({"name": z.name, "id": z.id, "description": z.description})
				
			data.append({"name": su.name, "id": su.id, "zones": zones})
		
		return {'status': 'success', 'data': data}





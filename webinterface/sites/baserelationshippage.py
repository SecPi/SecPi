import cherrypy
from tools import utils


class BaseRelationshipPage(object):
	
	def __init__(self, leftclass, leftclassname, rightclass, rightclassname):
		self.lclass = leftclass
		self.lclname = leftclassname
		self.rclass = rightclass
		self.rclname = rightclassname

	@property
	def db(self):
		return cherrypy.request.db

	@property
	def lookup(self):
		return cherrypy.request.lookup

	@cherrypy.expose()
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def add(self):
		if(hasattr(cherrypy.request, 'json')):
			left_id = cherrypy.request.json[self.lclname+'_id']
			right_id = cherrypy.request.json[self.rclname+'_id']
			
			if(left_id and left_id > 0 and right_id and right_id > 0):
				left = self.db.query(self.lclass).get(left_id)
				right = self.db.query(self.rclass).get(right_id)
				
				getattr(left, self.rclname+"s").append(right)
				self.db.commit()
				return {'status': 'success', 'message': 'Added %s to %s'%(right.name, left.name)}
			
		
		return {'status': 'error', 'message': 'Invalid IDs'}

	@cherrypy.expose()
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def delete(self):
		if(hasattr(cherrypy.request, 'json')):
			left_id = cherrypy.request.json[self.lclname+'_id']
			right_id = cherrypy.request.json[self.rclname+'_id']
			
			if(left_id and left_id > 0 and right_id and right_id > 0):
				left = self.db.query(self.lclass).get(left_id)
				right = self.db.query(self.rclass).get(right_id)
				
				getattr(left, self.rclname+"s").remove(right)
				self.db.commit()
				return {'status': 'success', 'message': 'Removed %s from %s'%(right.name, left.name)}
			
		
		return {'status': 'error', 'message': 'Invalid IDs'}

	@cherrypy.expose()
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def list(self):
		lefts = self.db.query(self.lclass).all()
		
		data = []
		
		for l in lefts:
			rights = []
			for r in getattr(l, self.rclname+"s"):
				rights.append({"name": r.name, "id": r.id})
				
			data.append({"name": l.name, "id": l.id, self.rclname+"s": rights})
		
		return {'status': 'success', 'data': data}

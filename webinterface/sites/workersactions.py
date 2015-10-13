# web framework
import cherrypy

# our stuff
from tools.db import objects
from tools import config
from tools import utils



class WorkersActionsPage():
	

	@property
	def db(self):
		return cherrypy.request.db

	'''
{
	"worker_id": 1,
	"action_id": 2	
}
	'''
	@cherrypy.expose()
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def add(self):
		if(hasattr(cherrypy.request, 'json')):
			worker_id = cherrypy.request.json['worker_id']
			action_id = cherrypy.request.json['action_id']
			
			if(worker_id and worker_id > 0 and action_id and action_id > 0):
				worker = self.db.query(objects.Worker).get(worker_id)
				action = self.db.query(objects.Action).get(action_id)
				
				worker.actions.append(action)
				self.db.commit()
				return {'status': 'success', 'message': 'Added Action %s to Worker %s!'%(worker.name, action.name)}
			
		
		return {'status': 'error', 'message': 'Invalid IDs!'}

	@cherrypy.expose()
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def delete(self):
		if(hasattr(cherrypy.request, 'json')):
			worker_id = cherrypy.request.json['worker_id']
			action_id = cherrypy.request.json['action_id']
			
			if(worker_id and worker_id > 0 and action_id and action_id > 0):
				worker = self.db.query(objects.Worker).get(worker_id)
				action = self.db.query(objects.Action).get(action_id)
				
				worker.actions.remove(action)
				self.db.commit()
				return {'status': 'success', 'message': 'Removed Action %s from Worker %s!'%(worker.name, action.name)}
			
		
		return {'status': 'error', 'message': 'Invalid IDs!'}


	@cherrypy.expose()
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out(handler=utils.json_handler)
	def list(self):
		workers = self.db.query(objects.Worker).all()
		
		data = []
		
		for w in workers:
			actions = []
			for a in w.actions:
				actions.append({"name": a.name, "id": a.id, "description": a.description})
				
			data.append({"name": w.name, "id": w.id, "actions": actions})
		
		return {'status': 'success', 'data': data}





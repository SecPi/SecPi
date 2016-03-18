import logging
import requests

from tools.notifier import Notifier

class SparkNotifier(Notifier):

	def __init__(self, id, params):
		super(SparkNotifier, self).__init__(id, params)
		if(not 'personal_token' in params or not 'room' in params):
			self.corrupted = True
			logging.error("Token or room name missing!")
			return
			
		
	def notify(self, info):
		if(not self.corrupted):
			logging.debug("Sending Cisco Spark notification!")
			
			room_name = self.params['room']
			auth_header = {'Authorization': 'Bearer %s'%self.params['personal_token']}

			# get room id
			rooms_req = requests.get('https://api.ciscospark.com/v1/rooms', headers=auth_header)
			rooms = rooms_req.json()
			room = [r for r in rooms['items'] if r['title'] == room_name]

			if(len(room)>0):
				# we got a room
				room_id = room[0]['id']
				logging.debug("Got existing room!")
			else:	
				# if not exists, create it
				logging.debug("No room found, creating one!")
				new_room_req = requests.post('https://api.ciscospark.com/v1/rooms', headers=auth_header, data={'title': room_name})
				new_room = new_room_req.json()
				
				room_id = new_room['id']
				
			if(room_id!=None):
				logging.debug("Found room: %s"%room_id)
				info_str = "Recieved alarm on sensor %s from worker %s: %s"%(info['sensor'], info['worker'], info['message'])
				noti_req = requests.post('https://api.ciscospark.com/v1/messages', headers=auth_header, data={'roomId': room_id, 'text': info_str})
				
			else:
				logging.error("No room found!")
		else:
			logging.error("Cisco Spark Notifier corrupted! No authorization code or room name given as parameter.")
		
	def cleanup(self):
		logging.debug("Cisco Spark Notifier: No cleanup necessary at the moment.")
		
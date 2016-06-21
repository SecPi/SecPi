import logging

from slacker import Slacker

from tools.notifier import Notifier

class SlackNotifier(Notifier):

	def __init__(self, id, params):
		super(SlackNotifier, self).__init__(id, params)
		if(not 'bot_token' in params or not 'channel' in params):
			self.corrupted = True
			logging.error("Slack: Token or channel name missing!")
			return
			
		
	def notify(self, info):
		if(not self.corrupted):
			try:
				logging.debug("Sending Slack notification!")
				
				channel_name = self.params['channel']
				slack = Slacker(self.params['bot_token'])
				
				# groups are private chats
				channels = slack.groups.list(1) # 1 --> exclude archived
				channel = [c for c in channels.body['groups'] if c['name'] == channel_name]

				if(len(channel)>0):
					# we got a channel
					channel_id = channel[0]['id']
					logging.debug("Got existing channel!")
				else:	
					# if not exists, create it
					logging.debug("No channel found, creating one!")
					new_channel_req = slack.groups.create(channel_name)
					
					channel_id = new_channel_req.body['group']['id']
					
				if(channel_id!=None):
					logging.debug("Found channel: %s"%channel_id)
					info_str = "Recieved alarm on sensor %s from worker %s: %s"%(info['sensor'], info['worker'], info['message'])
					slack.chat.post_message(channel_name, info_str)
					
				else:
					logging.error("No channel found!")
			except KeyError as ke:
				logging.error("Error in Slack Notifier: %s"%ke)
				
		else:
			logging.error("Slack Notifier corrupted! No token or channel name given as parameter.")
		
	def cleanup(self):
		logging.debug("Slack Notifier: No cleanup necessary at the moment.")
		
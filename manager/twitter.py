import logging
import tweepy

from tools.notifier import Notifier

class Twitter(Notifier):

	def __init__(self, id, params):
		super(Twitter, self).__init__(id, params)

		self.consumer_key = params["consumer_key"]
		self.consumer_secret = params["consumer_secret"]
		self.access_token = params["access_token"]
		self.access_token_secret = params["access_token_secret"]
		self.recipient = params["recipient"]

		auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
		auth.set_access_token(self.access_token, self.access_token_secret)

		self.api = tweepy.API(auth)
		logging.info("Twitter: Notifier initialized")


	def notify(self, info):
		info_str = "Recieved alarm on sensor %s from worker %s: %s"%(info['sensor'], info['worker'], info['message'])

		try:
			self.api.send_direct_message(self.recipient,text=info_str)
		except tweepy.error.TweepError, t:
			logging.error("Wasn't able to send message: %s" % t)
			return

		logging.info("Twitter: Direct message sent")

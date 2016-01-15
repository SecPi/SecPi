import logging
import tweepy

from tools.notifier import Notifier

class Twitter(Notifier):

	def __init__(self, id, params):
		super(Twitter, self).__init__(id, params)

		try:
			self.consumer_key = params["consumer_key"]
			self.consumer_secret = params["consumer_secret"]
			self.access_token = params["access_token"]
			self.access_token_secret = params["access_token_secret"]
			self.recipients = [rec.strip() for rec in params["recipient"].split(",")]
		except KeyError, k:
			logging.error("Twitter: Error while trying to initialize notifier, it seems there is a config parameter missing: %s" % k)
			self.corrupted = True
			return

		try:
			auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
			auth.set_access_token(self.access_token, self.access_token_secret)

			self.api = tweepy.API(auth)
		except Exception, e:
			logging.error("Twitter: Error while trying to initialize notifier: %s" % e)
			self.corrupted = True
			return
			
		logging.info("Twitter: Notifier initialized")


	def notify(self, info):
		if not self.corrupted:
			info_str = "Recieved alarm on sensor %s from worker %s: %s"%(info['sensor'], info['worker'], info['message'])

			try:
				for recipient in self.recipients:
					self.api.send_direct_message(recipient,text=info_str)
					logging.info("Twitter: Message to %s was sent successfully" % recipient)
			except tweepy.error.TweepError, t:
					logging.error("Twitter: Wasn't able to send message to %s: %s" % (recipient, t))
		else:
			logging.error("Twitter: Wasn't able to notify because there was an initialization error")
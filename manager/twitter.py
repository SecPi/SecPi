import logging

import tweepy

from secpi.model.notifier import Notifier

logger = logging.getLogger(__name__)


class Twitter(Notifier):
    def __init__(self, id, params):
        super(Twitter, self).__init__(id, params)

        try:
            self.consumer_key = params["consumer_key"]
            self.consumer_secret = params["consumer_secret"]
            self.access_token = params["access_token"]
            self.access_token_secret = params["access_token_secret"]
            self.recipients = [rec.strip() for rec in params["recipients"].split(",")]
        except KeyError as ke:
            logger.error(
                "Twitter: Error while trying to initialize notifier, it seems there is a config parameter missing: %s"
                % ke
            )
            self.corrupted = True
            return

        try:
            auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
            auth.set_access_token(self.access_token, self.access_token_secret)

            self.api = tweepy.API(auth)
        except Exception as e:
            logger.error("Twitter: Error while trying to initialize notifier: %s" % e)
            self.corrupted = True
            return

        logger.info("Twitter: Notifier initialized")

    def notify(self, info):
        if not self.corrupted:
            info_str = "Recieved alarm on sensor %s from worker %s: %s" % (
                info["sensor"],
                info["worker"],
                info["message"],
            )

            try:
                for recipient in self.recipients:
                    self.api.send_direct_message(recipient, text=info_str)
                    logger.info(f"Twitter: Message to {recipient} was sent successfully")
            except tweepy.TweepyException:
                logger.exception(f"Twitter: Sending message to {recipient} failed")
        else:
            logger.error("Twitter: Wasn't able to notify because there was an initialization error")

    def cleanup(self):
        logger.debug("Twitter: No cleanup necessary at the moment")

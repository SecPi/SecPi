import logging
import gsmmodem # TODO: add to requirements.txt

from tools.notifier import Notifier


class Sms(Notifier):

	def __init__(self, id, params):
		super(Sms, self).__init__(id, params)

		self.port = params["port"]
		self.baud = params["baud"]
		self.pin = params["pin"]
		self.recipient = params["recipient"] # TODO: change to list

		self.modem = GsmModem(self.port, self.baud)
		try:
			self.modem.connect(self.pin)
		except gsmmodem.exceptions.PinRequiredError:
			logging.exception("Sms: SIM PIN required")
			self.corrupted = True
		except gsmmodem.exceptions.IncorrectPinError:
			logging.exception("Sms: SIM PIN is wrong")
			self.corrupted = True

		try: # maybe move this to notify?
			self.modem.waitForNetworkCoverage(10) #timeout
		except gsmmodem.exceptions.TimeoutException:
			logging.exception("Sms: Timeout, wasn't able to get network connection")
			self.corrupted = True # TODO: introduce network state and try to reconnect

		#self.modem.close()
		logging.info("Sms: Notifier initialized")


	def notify(self, info):
		if not self.corrupted:
			info_str = "Recieved alarm on sensor %s from worker %s: %s"%(info['sensor'], info['worker'], info['message'])
			# TODO: make for loop if there are multiple recipients
			try:
				success = self.modem.sendSms(recipient, info_str, waitForDeliveryReport=True)
			except gsmmodem.exceptions.TimeoutException:
				logging.exception("Sms: Timeout, failed to send message")
				return

			logging.info("Sms: Message to XXXXX was sent successfully")
		else:
			logging.error("Sms: Wasn't able to notify because there was an initialization error")
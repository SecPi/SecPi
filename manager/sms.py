import logging
import gsmmodem # TODO: add to requirements.txt and usb_modeswitch to debian dependencies
import serial.serialutil

from tools.notifier import Notifier

class Sms(Notifier):

	def __init__(self, id, params):
		super(Sms, self).__init__(id, params)

		try:
			self.port = params["port"]
			self.baud = int(params.get("baud", 115200))
			self.network_timeout = int(params.get("network_timeout", 60))
			self.pin = params.get("pin", None)
			self.recipients = [rec.strip() for rec in params["recipients"].split(",")]
		except KeyError as ke: # if config parameters are missing
			logging.error("Sms: Wasn't able to initialize the notifier, it seems there is a config parameter missing: %s" % ke)
			self.corrupted = True
			return
		except ValueError as ve: # if one configuration parameter can't be parsed as int
			logging.error("Sms: Wasn't able to initialize the notifier, please check your configuration: %s" % ve)
			self.corrupted = True
			return

		# Initialization of modem
		self.modem = gsmmodem.GsmModem(self.port, self.baud)
		try:
			self.modem.connect(self.pin)
		except gsmmodem.exceptions.PinRequiredError: # PIN required
			logging.exception("Sms: SIM PIN required")
			self.corrupted = True
		except gsmmodem.exceptions.IncorrectPinError: # wrong PIN
			logging.exception("Sms: SIM PIN is wrong")
			self.corrupted = True
		except gsmmodem.exceptions.TimeoutException: # maybe because it can't access the sim? not sure yet
			logging.exception("Sms: Timeout while establishing serial connection to usb modem")
			self.corrupted = True
		except serial.serialutil.SerialException: # wrong device path or no modem plugged in
			logging.exception("Sms: Wasn't able to open specified port")
			self.corrupted = True
		except gsmmodem.exceptions.CmeError: # no SIM inside?
			logging.exception("Sms: Wasn't able to access SIM, maybe there is none?")
			self.corrupted = True
		else:
			logging.info("Sms: Notifier initialized")


	def notify(self, info):
		if not self.corrupted:
			# first we have to get a signal/network coverage
			try:
				self.modem.waitForNetworkCoverage(self.network_timeout)
			except gsmmodem.exceptions.TimeoutException: # when the modem is unable to connect to the cellular network
				logging.exception("Sms: Timeout, wasn't able to get network connection")
				return
			except Exception as e: # e.g. when unplugging the modem from the usb port
				logging.exception("Sms: An unknown error occured while trying to get network coverage: %s" % e)
				return

			# now we can try to send the message
			info_str = "SecPi: Recieved alarm on sensor %s from worker %s." % (info['sensor'], info['worker'])
			for recipient in self.recipients:
				try:
					logging.debug("Sms: Sending message to %s" % recipient)
					success = self.modem.sendSms(recipient, info_str, waitForDeliveryReport=False)
				except gsmmodem.exceptions.TimeoutException: # timeout when sending the sms
					logging.exception("Sms: Timeout, failed to send message to %s" % recipient)
				except gsmmodem.exceptions.CmsError: # e.g. when the specified number is invalid (containing a letter, ...)
					logging.exception("Sms: Wasn't able to send message to %s, please check the number" % recipient)
				except Exception as e:
					logging.exception("Sms: An unknown error occured while sending a message to %s: %s" % (recipient, e))
				else:
					logging.info("Sms: Message to %s was sent successfully" % recipient)
		else:
			logging.error("Sms: Wasn't able to notify because there was an initialization error")

	def cleanup(self):
		try:
			self.modem.close()
		except Exception as e:
			logging.exception("Sms: Wasn't able to cleanup modem: %s" % e)
		else:
			logging.debug("Sms: cleanup successful")

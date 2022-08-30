import RPi.GPIO as GPIO
import logging
import time

from tools.action import Action


logger = logging.getLogger(__name__)


class Buzzer(Action):

	def __init__(self, id, params, worker):
		super(Buzzer, self).__init__(id, params, worker)
		try:
			self.duration = int(params["duration"])
			self.gpio_pin = int(params["gpio_pin"])
		except KeyError as ke: # if config parameters are missing in file
			logger.error("Buzzer: Wasn't able to initialize the device, it seems there is a config parameter missing: %s" % ke)
			self.corrupted = True
			return
		except ValueError as ve: # if a parameter can't be parsed as int
			logger.error("Buzzer: Wasn't able to initialize the device, please check your configuration: %s" % ve)
			self.corrupted = True
			return

		try:
			GPIO.setmode(GPIO.BCM)
			GPIO.setup(self.gpio_pin, GPIO.OUT)
		except ValueError as ve: # GPIO pin number is not in valid range
			logger.error("Buzzer: The given pin number is not in a valid range: %s" % ve)
			self.corrupted = True
			return
		logger.debug("Buzzer: Audio device initialized")

	def buzz(self, duration):
		logger.debug("Buzzer: Trying to make some noise")
		start_time = time.time()
		state = True
		while (time.time() - start_time) < duration:
			GPIO.output(self.gpio_pin, state)
			if state:
				state = False
				time.sleep(0.5)
			else:
				state = True
				time.sleep(0.05)
		
		state = False
		GPIO.output(self.gpio_pin, state)
		logger.debug("Buzzer: Finished making noise")

	def execute(self):
		if not self.corrupted:
			self.buzz(self.duration)
		else:
			logger.error("Buzzer: Wasn't able to make noise because of an initialization error")


	def cleanup(self):
		if not self.corrupted:
			try:
				GPIO.cleanup(self.gpio_pin)
			except ValueError as ve: # GPIO pin number is not in valid range
				logger.error("Buzzer: The given pin number is not in a valid range: %s" % ve)
			else:
				logger.debug("Buzzer: Cleaned up buzzer action")

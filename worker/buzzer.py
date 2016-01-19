import RPi.GPIO as GPIO
import logging
import time

from tools.action import Action

class Buzzer(Action):

	def __init__(self, id, params):
		super(Buzzer, self).__init__(id, params)
		try:
			self.duration = int(params["duration"])
			self.gpio_pin = int(params["gpio_pin"])
		except KeyError as k: # if config parameters are missing in file
			logging.error("Buzzer: Wasn't able to initialize the device, it seems there is a config parameter missing: %s" % k)
			self.corrupted = True
			return
		except ValueError as v: # if a parameter can't be parsed as int
			logging.error("Buzzer: Wasn't able to initialize the device, please check your configuration: %s" % v)
			self.corrupted = True
			return

		try:
			GPIO.setmode(GPIO.BCM)
			GPIO.setup(self.gpio_pin, GPIO.OUT)
		except ValueError as v: # GPIO pin number is not in valid range
			logging.error("Buzzer: The given pin number is not in a valid range: %s" % v)
			self.corrupted = True
			return
		logging.debug("Buzzer: Audio device initialized")

	def buzz(self, duration):
		logging.debug("Buzzer: Trying to make some noise")
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
		logging.debug("Buzzer: Finished making noise")

	def execute(self):
		if not self.corrupted:
			self.buzz(self.duration)
		else:
			logging.error("Buzzer: Wasn't able to make noise because of an initialization error")


	def cleanup(self):
		if not self.corrupted:
			GPIO.cleanup(self.gpio_pin)

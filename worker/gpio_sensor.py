from tools.sensor import Sensor
import logging

import RPi.GPIO as GPIO

class GPIOSensor(Sensor):
	
	def __init__(self, id, params, worker):
		super(GPIOSensor, self).__init__(id, params, worker)
		self.active = False
		try:
			self.gpio = int(params["gpio"])
			self.bouncetime = int(self.params['bouncetime'])
		except ValueError as ve: # if one configuration parameter can't be parsed as int
			self.post_err("GPIOSensor: Wasn't able to initialize the sensor, please check your configuration: %s" % ve)
			self.corrupted = True
			return
		except KeyError as ke: # if config parameters are missing in the file
			self.post_err("GPIOSensor: Wasn't able to initialize the sensor, it seems there is a config parameter missing: %s" % ke)
			self.corrupted = True
			return
		
		GPIO.setmode(GPIO.BCM)
		logging.debug("GPIOSensor: Sensor initialized")
	
	def setup_sensor(self):
		try:
			GPIO.setup(self.gpio, GPIO.IN)
			GPIO.add_event_detect(self.gpio, GPIO.RISING, callback=self.cb_alarm, bouncetime=self.bouncetime)
		except ValueError as ve: # GPIO pin number or bouncetime is not in valid range
			self.post_err("GPIOSensor: The given pin number or bouncetime is not in a valid range: %s" % ve)
			return
		logging.debug("GPIOSensor: Registered sensor at pin %s!" % self.gpio)
	
	def cleanup_sensor(self):
		try:
			GPIO.remove_event_detect(self.gpio)
			GPIO.cleanup(self.gpio)
		except ValueError as ve: # GPIO pin number is not in valid range
			self.post_err("GPIOSensor: The given pin number is not in a valid range: %s" % ve)
		logging.debug("GPIOSensor: Removed sensor at pin %s!" % self.gpio)
	
	# callback for alarm
	def cb_alarm(self, channel):
		if(self.active):
			self.alarm("GPIO sensor at pin %s detected something!" % channel)
	
	def activate(self):
		if not self.corrupted:
			self.active = True
			self.setup_sensor()
		else:
			self.post_err("GPIOSensor: Sensor couldn't be activated")

	def deactivate(self):
		if not self.corrupted:
			self.active = False
			self.cleanup_sensor()
		else:
			self.post_err("GPIOSensor: Sensor couldn't be deactivated") # maybe make this more clear
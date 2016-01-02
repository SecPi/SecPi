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
		except ValueError, v: # if one configuration parameter can't be parsed as int
			logging.error("GPIOSensor: Wasn't able to initialize the sensor, please check your configuration: %s" % v)
			self.corrupted = True
			return
		except KeyError, k: # if config parameters are missing in the file
			logging.error("GPIOSensor: Wasn't able to initialize the sensor, it seems there is a config parameter missing: %s" % k)
			self.corrupted = True
			return
		
		GPIO.setmode(GPIO.BCM)
		logging.debug("GPIOSensor: Sensor initialized")
	
	def setup_sensor(self):
		try:
			GPIO.setup(self.gpio, GPIO.IN)
			GPIO.add_event_detect(self.gpio, GPIO.RISING, callback=self.cb_alarm, bouncetime=self.bouncetime)
		except ValueError, v: # GPIO pin number or bouncetime is not in valid range
			logging.error("GPIOSensor: The given pin number or bouncetime is not in a valid range: %s" % v)
			return
		logging.debug("GPIOSensor: Registered sensor at pin %s!" % self.gpio)
	
	def cleanup_sensor(self):
		try:
			GPIO.remove_event_detect(self.gpio)
			GPIO.cleanup(self.gpio)
		except ValueError, v: # GPIO pin number is not in valid range
			logging.error("GPIOSensor: The given pin number is not in a valid range: %s" % v)
		logging.debug("GPIOSensor: Removed sensor at pin %s!" % self.gpio)
	
	# callback for alarm
	def cb_alarm(self, channel):
		if(self.active):
			self.alarm("GPIO sensor at pin %s activated!" % channel)
	
	def activate(self):
		if not self.corrupted:
			self.active = True
			self.setup_sensor()
		else:
			logging.error("GPIOSensor: Sensor couldn't be activated")

	def deactivate(self):
		if not self.corrupted:
			self.active = False
			self.cleanup_sensor()
		else:
			logging.error("GPIOSensor: Sensor couldn't be deactivated") # maybe make this more clear
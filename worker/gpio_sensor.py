from tools.sensor import Sensor

import RPi.GPIO as GPIO

class GPIOSensor(Sensor):
	
	def __init__(self, id, params, worker):
		super(GPIOSensor, self).__init__(id, params, worker)
		# setup gpio and logging
		GPIO.setmode(GPIO.BCM)
		
		self.active = False
	
	def setup_sensor(self):
		if(int(self.params["gpio"])>=0):
			GPIO.setup(int(self.params["gpio"]), GPIO.IN)
			GPIO.add_event_detect(int(self.params["gpio"]), GPIO.RISING, callback=self.cb_alarm, bouncetime=int(self.params['bouncetime']))
#			logging.info("Registered sensor at pin %s!"%(self.params["gpio"]))
	
	def cleanup_sensor(self):
		GPIO.remove_event_detect(int(self.params["gpio"]))
		#GPIO.cleanup(int(self.params["gpio"]))
#		logging.debug("Removed sensor at pin %s!" % self.params["gpio"])
	
	# callback for alarm
	def cb_alarm(self, channel):
		if(self.active):
			self.alarm("GPIO sensor at pin %s activated!"%channel)
	
	def activate(self):
		self.active = True
		self.setup_sensor()
		return

	def deactivate(self):
		self.active = False
		self.cleanup_sensor()
		return

import RPi.GPIO as GPIO
import time

from tools.action import Action

class Buzzer(Action):

	def __init__(self, id, params):
		super(Buzzer, self).__init__(id, params)
		self.duration = int(params["duration"])
		self.gpio_pin = int(params["gpio_pin"])
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.gpio_pin, GPIO.OUT)

	def buzz(self, duration):
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
		# set output to low again, because cleanup doesn't work yet
		state = False
		GPIO.output(self.gpio_pin, state)
		print "finished buzzing"
	# TODO: implement cleanup for gpio

	def execute(self):
		self.buzz(self.duration)
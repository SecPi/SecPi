import RPi.GPIO as GPIO
import time
import datetime

GPIO.setmode(GPIO.BCM)
PIR_PIN = 17
GPIO.setup(PIR_PIN, GPIO.IN)

def alarm(channel):
	print "Sensor %s detected something." % channel	


GPIO.add_event_detect(PIR_PIN, GPIO.RISING, callback=alarm)


while True:
	time.sleep(100)


GPIO.cleanup()

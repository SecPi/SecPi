import time

import RPi.GPIO as GPIO

led = 7
right_button = 10
left_button = 8
status = 1

GPIO.setmode(GPIO.BOARD)
GPIO.setup(led, GPIO.OUT)
GPIO.setup(right_button, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(left_button, GPIO.IN, GPIO.PUD_UP)


def toggleLED(channel):
    global status
    if status == 0:
        status = 1
    else:
        status = 0

    GPIO.output(led, status)


GPIO.add_event_detect(left_button, GPIO.RISING, callback=toggleLED, bouncetime=300)


# GPIO.output(led, 1)
# time.sleep(5)
# GPIO.output(led, 0)

while True:
    GPIO.wait_for_edge(right_button, GPIO.FALLING)
    break
# 	if GPIO.input(left_button) == False:
# 	GPIO.wait_for_edge(23, GPIO.RISING)
# 		print("Left button pressed")
# 		if status == 0:
# 			status = 1
# 		else:
# 			status = 0
#
# 		GPIO.output(led, status)
#
# 	if GPIO.input(right_button) == False:
# 		print("Right button pressed")
# 		break


GPIO.cleanup()

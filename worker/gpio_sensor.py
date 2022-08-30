import logging

import RPi.GPIO as GPIO

from secpi.model.sensor import Sensor

logger = logging.getLogger(__name__)


class GPIOSensor(Sensor):
    def __init__(self, id, params, worker):
        logger.info(f"Initializing sensor id={id} with parameters {params}")
        super(GPIOSensor, self).__init__(id, params, worker)
        self.active = False
        try:
            self.gpio = int(params["gpio"])
            self.bouncetime = int(self.params["bouncetime"])
            self.edge = self.params.get("edge", "rising").lower()
            if self.edge not in ["rising", "falling", "both"]:
                raise ValueError("GPIOSensor: Parameter 'edge' must be one of ['rising', 'falling', 'both']")
        except ValueError as ve:  # if one configuration parameter can't be parsed as int
            self.post_err("GPIOSensor: Wasn't able to initialize the sensor, please check your configuration: %s" % ve)
            self.corrupted = True
            return
        except KeyError as ke:  # if config parameters are missing in the file
            self.post_err(
                "GPIOSensor: Wasn't able to initialize the sensor, it seems there is a config parameter missing: %s"
                % ke
            )
            self.corrupted = True
            return

        GPIO.setmode(GPIO.BCM)
        logger.debug("GPIOSensor: Sensor initialized")

    def setup_sensor(self):
        try:
            GPIO.setup(self.gpio, GPIO.IN)
            if self.edge == "rising":
                edge_type = GPIO.RISING
            elif self.edge == "falling":
                edge_type = GPIO.FALLING
            elif self.edge == "both":
                edge_type = GPIO.BOTH
            else:
                raise ValueError("GPIOSensor: Unknown edge type: %s" % self.edge)
            GPIO.add_event_detect(self.gpio, edge_type, callback=self.cb_alarm, bouncetime=self.bouncetime)
        except ValueError as ve:  # GPIO pin number or bouncetime is not in valid range
            self.post_err("GPIOSensor: The given pin number or bouncetime is not in a valid range: %s" % ve)
            return
        logger.debug("GPIOSensor: Registered sensor at pin %s" % self.gpio)

    def cleanup_sensor(self):
        try:
            GPIO.remove_event_detect(self.gpio)
            GPIO.cleanup(self.gpio)
        except ValueError as ve:  # GPIO pin number is not in valid range
            self.post_err("GPIOSensor: The given pin number is not in a valid range: %s" % ve)
        logger.debug("GPIOSensor: Removed sensor at pin %s" % self.gpio)

    # callback for alarm
    def cb_alarm(self, channel):
        if self.active:
            if self.edge in ["rising", "falling"]:
                self.alarm("GPIO sensor at pin %s detected something" % channel)
            else:
                if GPIO.input(channel):
                    state = "activated"
                else:
                    state = "deactivated"
                self.alarm("GPIO sensor at pin %s %s" % (channel, state))

    def activate(self):
        if not self.corrupted:
            self.active = True
            self.setup_sensor()
            self.post_log(f"GPIOSensor: Sensor activated successfully, id={self.id}")
        else:
            self.post_err(f"GPIOSensor: Sensor could not be activated, id={self.id}")

    def deactivate(self):
        if not self.corrupted:
            self.active = False
            self.cleanup_sensor()
            self.post_log(f"GPIOSensor: Sensor deactivated successfully, id={self.id}")
        else:
            # maybe make this more clear
            self.post_err(f"GPIOSensor: Sensor could not be deactivated, id={self.id}")

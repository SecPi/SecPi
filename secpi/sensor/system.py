import logging
import os
import threading
import time

from secpi.model.sensor import Sensor

logger = logging.getLogger(__name__)


class SystemTemperature(Sensor):  # DS18B20 digital temperature sensor
    def __init__(self, id, params, worker):
        logger.info(f"Initializing sensor id={id} with parameters {params}")
        super(SystemTemperature, self).__init__(id, params, worker)
        # self.active = False
        try:
            self.min = int(params["min"])
            self.max = int(params["max"])
            self.bouncetime = int(params["bouncetime"])
            self.device_id = params["device_id"]
        except ValueError as ve:  # if one configuration parameter can't be parsed as int
            self.post_err(
                "SystemTemperature: Wasn't able to initialize the sensor, please check your configuration: %s" % ve
            )
            self.corrupted = True
            return
        except KeyError as ke:  # if config parameters are missing
            self.post_err(
                "SystemTemperature: Initializing the sensor failed, it seems there is a config parameter missing: %s"
                % ke
            )
            self.corrupted = True
            return

        os.system("modprobe w1-gpio")
        os.system("modprobe w1-therm")

        base_dir = "/sys/bus/w1/devices/"
        # device_folder = glob.glob(base_dir + '28*')[0]
        self.device_file = base_dir + self.device_id + "/w1_slave"

        if not os.path.isfile(self.device_file):  # if there is no slave file which contains the temperature
            self.corrupted = True
            self.post_err("SystemTemperature: Wasn't able to find temperature file at %s" % self.device_file)
            return

        logger.info("SystemTemperature: Sensor initialized")

    def activate(self):
        if not self.corrupted:
            self.stop_thread = False
            self.checker_thread = threading.Thread(
                name="thread-checker-%s" % self.device_id, target=self.check_temperature
            )
            self.checker_thread.start()
            self.post_log(f"SystemTemperature: Sensor activated successfully, id={self.id}")
        else:
            self.post_err(f"SystemTemperature: Sensor could not be activated, id={self.id}")

    def deactivate(self):
        if not self.corrupted:
            self.stop_thread = True
            self.post_log(f"SystemTemperature: Sensor deactivated successfully, id={self.id}")
        else:
            self.post_err(f"SystemTemperature: Sensor could not be deactivated, id={self.id}")

    def check_temperature(self):
        while True:
            if self.stop_thread:  # exit thread when flag is set
                return

            current_temp = self.read_temp()
            if current_temp < self.min or current_temp > self.max:
                self.alarm("Temperature is not in valid range: %s" % current_temp)
                time.sleep(self.bouncetime)
                continue
            time.sleep(3)

    def read_temp_raw(self):
        with open(self.device_file, "r") as f:
            lines = f.readlines()

        return lines

    def read_temp(self):
        lines = self.read_temp_raw()
        while lines[0].strip()[-3:] != "YES":
            time.sleep(0.2)
            lines = self.read_temp_raw()
        equals_pos = lines[1].find("t=")
        if equals_pos != -1:
            begin = equals_pos + 2
            temp_string = lines[1][begin:]
            temp_c = float(temp_string) / 1000.00
        return temp_c

import logging
import threading
import time

from ping3 import ping

from secpi.model.sensor import Sensor

logger = logging.getLogger(__name__)


class Pinger(Sensor):
    def __init__(self, identifier, params, worker):
        logger.info(f"Initializing sensor id={identifier} with parameters {params}")
        super().__init__(identifier, params, worker)

        try:
            self.interval = float(params["interval"])
            self.max_losses = int(params["max_losses"])
            self.destination_ip = params["destination_ip"]
            self.bouncetime = int(params["bounce_time"])
        except KeyError as ke:  # if config parameters are missing in file
            self.post_err("Pinger: Wasn't able to initialize, it seems there is a config parameter missing: %s" % ke)
            self.corrupted = True
            return
        except ValueError as ve:  # if a parameter can't be parsed as int
            self.post_err("Pinger: Wasn't able to initialize, please check your configuration: %s" % ve)
            self.corrupted = True
            return

        logger.debug("Pinger: Sensor initialized")

    def activate(self):
        if not self.corrupted:
            self.stop_thread = False
            self.pinger_thread = threading.Thread(name="thread-pinger-%s" % self.destination_ip, target=self.check_up)
            self.pinger_thread.start()
            self.post_log(f"Pinger: Sensor activated successfully, id={self.identifier}")
        else:
            self.post_err(f"Pinger: Sensor could not be activated, id={self.identifier}")

    def deactivate(self):
        if not self.corrupted:
            self.stop_thread = True
            self.post_log(f"Pinger: Sensor deactivated successfully, id={self.identifier}")
        else:
            self.post_err(f"Pinger: Sensor could not be deactivated, id={self.identifier}")

    def check_up(self):
        losses = 0
        while True:
            if self.stop_thread:
                return

            if not ping(self.destination_ip):
                losses += 1
                logger.info("Pinger: Loss happened, %d/%d" % (losses, self.max_losses))
            else:
                losses = 0

            if losses >= self.max_losses:
                self.alarm("%d consecutive pings were lost" % losses)
                losses = 0
                time.sleep(self.bouncetime)
                continue
            time.sleep(self.interval)

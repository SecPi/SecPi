import abc
import logging

from secpi.model import constants

logger = logging.getLogger(__name__)


class Sensor:
    def __init__(self, identifier, params, worker):
        self.identifier = identifier
        self.params = params
        self.worker = worker
        self.corrupted = False

    def alarm(self, message):
        self.worker.alarm(self.identifier, message)

    def post_log(self, msg, lvl=constants.LEVEL_INFO):
        self.worker.post_log(msg, lvl)

    def post_err(self, msg):
        self.worker.post_err(msg)

    @abc.abstractmethod
    def activate(self):
        """Activate the sensor."""
        return

    @abc.abstractmethod
    def deactivate(self):
        """Deactivate the sensor."""
        return

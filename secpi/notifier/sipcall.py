"""
About
=====

SIP notifier adapter for placing calls through Asterisk, using `pycall`.

- https://www.asterisk.org/
- https://pypi.org/project/pycall/


Setup
=====
::

    # Install prerequisites, using `pip`.
    pip install pycall

"""
import logging

from pycall import Call, CallFile, Context

from secpi.model.message import NotificationMessage
from secpi.model.notifier import Notifier

logger = logging.getLogger(__name__)


class SipCall(Notifier):
    def __init__(self, identifier, params):
        super().__init__(identifier, params)

        try:
            self.sip_number = params["sip_number"]
            self.sip_route = params["sip_route"]
            self.asterisk_spool_dir = params.get("sip_asterisk_spool_dir")
            # self.sip_context = params["sip_context"]
            # self.sip_application = params["sip_application"]
        except KeyError as ex:
            logger.error(f"SipCall: Initializing notifier failed, configuration parameter missing: {ex}")
            self.corrupted = True
            return

        if not self.sip_number.startswith("+"):
            self.sip_number = "+" + self.sip_number

        logger.info("SipCall: Notifier initialized")

    def notify(self, info: NotificationMessage):
        if not self.corrupted:
            logger.info(f"SipCall: Starting call to {self.sip_number}, triggered by sensor {info.sensor_name}")
            context = f"alarm_{info.sensor_name}"
            try:
                self.sip_submit_call(self.sip_route, self.sip_number, context)
                logger.info(f"SipCall: Call to {self.sip_number} submitted successfully")
            except Exception:
                logger.exception(f"SipCall: Call to {self.sip_number} failed")
        else:
            logger.error("SipCall: Wasn't able to notify because there was an initialization error")

    def cleanup(self):
        logger.debug("SipCall: No cleanup necessary at the moment")

    def sip_submit_call(self, route, number, context):
        c = Call("SIP/%s/%s" % (route, number), wait_time=50, retry_time=120, max_retries=4)
        con = Context(context, "s", "1")
        cf = CallFile(c, con, user="asterisk", spool_dir=self.asterisk_spool_dir)
        cf.spool()

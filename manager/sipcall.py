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

from pycall import Application, Call, CallFile, Context
from tools.notifier import Notifier


class SipCall(Notifier):
    def __init__(self, id, params):
        super(SipCall, self).__init__(id, params)

        try:
            self.sip_number = params["sip_number"]
            self.sip_route = params["sip_route"]
            # self.sip_context = params["sip_context"]
            # self.sip_application = params["sip_application"]
        except KeyError as ke:
            logging.error(f"SipCall: Initializing notifier failed, configuration parameter missing: {ke}")
            self.corrupted = True
            return

        if not self.sip_number.startswith("+"):
            self.sip_number = "+" + self.sip_number

        logging.info("SipCall: Notifier initialized")

    def notify(self, info):
        if not self.corrupted:
            sensor_name = str(info["sensor"])
            logging.info(f"SipCall: Starting call to {self.sip_number}, triggered by sensor {sensor_name}")
            context = f"alarm_{sensor_name}"
            try:
                self.sip_submit_call(self.sip_route, self.sip_number, context)
                logging.info(f"SipCall: Call to {self.sip_number} submitted successfully")
            except Exception:
                logging.exception(f"SipCall: Call to {self.sip_number} failed")
        else:
            logging.error("SipCall: Wasn't able to notify because there was an initialization error")

    def cleanup(self):
        logging.debug("SipCall: No cleanup necessary at the moment")

    @staticmethod
    def sip_submit_call(route, number, context):
        c = Call("SIP/%s/%s" % (route, number), wait_time=50, retry_time=120, max_retries=4)
        con = Context(context, "s", "1")
        cf = CallFile(c, con, user="asterisk")
        cf.spool()

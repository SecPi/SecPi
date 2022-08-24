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
            # self.sip_recipients = [rec.strip() for rec in params["sip_recipients"].split(",")]
            self.sip_recipients = self.sip_number
            self.sip_route = params["sip_route"]
            # self.sip_context = params["sip_context"]
            # self.sip_application = params["sip_application"]
        except KeyError as ke:
            logging.error(
                "SipCall: Error while trying to initialize notifier, it seems there is a config parameter missing: %s"
                % ke
            )
            self.corrupted = True
            return
        logging.info("SipCall: Notifier initialized")

    def notify(self, info):
        if not self.corrupted:
            # info_str = "Recieved alarm on sensor %s from worker %s: %s"%(info['sensor'], info['worker'], info['message'])
            context = "alarm_" + str(info["sensor"])
            logging.info(str(info["sensor"]))
            if str(info["sensor"]) != "eisentuer":
                try:
                    # for recipient in self.recipients:
                    # call(self.sip_route, recipient, context)
                    number = "+" + self.sip_number
                    self.call(self.sip_route, number, context)
                    # logging.info("SipCall: Call to %s was sent" % recipient)
                    logging.info("SipCall: Call to %s was sent" % self.sip_number)
                except Exception as e:
                    # logging.error("SipCall: Wasn't able to sent call to %s: %s" % (recipient, e))
                    logging.error("SipCall: Wasn't able to sent call to %s: %s" % (self.sip_number, e))
        else:
            logging.error("SipCall: Wasn't able to notify because there was an initialization error")

    def cleanup(self):
        logging.debug("Asterisk: No cleanup necessary at the moment")

    def call(self, route, number, context):
        try:
            c = Call("SIP/%s/%s" % (route, number), wait_time=50, retry_time=120, max_retries=4)
            con = Context(context, "s", "1")
            cf = CallFile(c, con, user="asterisk")
            cf.spool()
        except Exception as e:
            logging.error("SipCall: Unknown call error: %s" % e)

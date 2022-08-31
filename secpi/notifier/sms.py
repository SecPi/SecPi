import logging

import gsmmodem
import gsmmodem.exceptions
import serial.serialutil

from secpi.model.notifier import Notifier

logger = logging.getLogger(__name__)


class Sms(Notifier):
    def __init__(self, id, params):
        super(Sms, self).__init__(id, params)

        try:
            self.port = params["port"]
            self.baud = int(params.get("baud", 115200))
            self.network_timeout = int(params.get("network_timeout", 60))
            self.pin = params.get("pin", None)
            self.recipients = [rec.strip() for rec in params["recipients"].split(",")]
        except KeyError as ke:  # if config parameters are missing
            logger.error(
                "Sms: Wasn't able to initialize the notifier, it seems there is a config parameter missing: %s" % ke
            )
            self.corrupted = True
            return
        except ValueError as ve:  # if one configuration parameter can't be parsed as int
            logger.error("Sms: Wasn't able to initialize the notifier, please check your configuration: %s" % ve)
            self.corrupted = True
            return

        # Initialization of modem
        self.modem = gsmmodem.GsmModem(self.port, self.baud)
        try:
            self.modem.connect(self.pin)
        except gsmmodem.exceptions.PinRequiredError:  # PIN required
            logger.exception("Sms: SIM PIN required")
            self.corrupted = True
        except gsmmodem.exceptions.IncorrectPinError:  # wrong PIN
            logger.exception("Sms: SIM PIN is wrong")
            self.corrupted = True
        except gsmmodem.exceptions.TimeoutException:  # maybe because it can't access the sim? not sure yet
            logger.exception("Sms: Timeout while establishing serial connection to usb modem")
            self.corrupted = True
        except serial.serialutil.SerialException:  # wrong device path or no modem plugged in
            logger.exception("Sms: Wasn't able to open specified port")
            self.corrupted = True
        except gsmmodem.exceptions.CmeError:  # no SIM inside?
            logger.exception("Sms: Wasn't able to access SIM, maybe there is none?")
            self.corrupted = True
        else:
            logger.info("Sms: Notifier initialized")

    def notify(self, info):
        if not self.corrupted:
            # first we have to get a signal/network coverage
            try:
                self.modem.waitForNetworkCoverage(self.network_timeout)
            except gsmmodem.exceptions.TimeoutException:  # when the modem is unable to connect to the cellular network
                logger.exception("Sms: Timeout, wasn't able to get network connection")
                return
            except Exception as e:  # e.g. when unplugging the modem from the usb port
                logger.exception("Sms: An unknown error occurred while trying to get network coverage: %s" % e)
                return

            # now we can try to send the message
            info_str = "SecPi: Recieved alarm on sensor %s from worker %s." % (info["sensor"], info["worker"])
            for recipient in self.recipients:
                try:
                    logger.debug("Sms: Sending message to %s" % recipient)
                    success = self.modem.sendSms(recipient, info_str, waitForDeliveryReport=False)

                # Timeout when sending the SMS.
                except gsmmodem.exceptions.TimeoutException:
                    logger.exception("Sms: Timeout, failed to send message to %s" % recipient)

                # When the specified number is invalid, e.g. containing a letter.
                except gsmmodem.exceptions.CmsError:
                    logger.exception("Sms: Wasn't able to send message to %s, please check the number" % recipient)

                except Exception as e:
                    logger.exception(
                        "Sms: An unknown error occurred while sending a message to %s: %s" % (recipient, e)
                    )
                else:
                    logger.info("Sms: Message to %s was sent successfully" % recipient)
        else:
            logger.error("Sms: Wasn't able to notify because there was an initialization error")

    def cleanup(self):
        try:
            self.modem.close()
        except Exception as e:
            logger.exception("Sms: Wasn't able to cleanup modem: %s" % e)
        else:
            logger.debug("Sms: cleanup successful")

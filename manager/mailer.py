import logging
import mimetypes
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.text import MIMEText

from tools.notifier import Notifier
from tools.utils import str_to_value

logger = logging.getLogger(__name__)


class Mailer(Notifier):
    def __init__(self, id, params):
        super(Mailer, self).__init__(id, params)

        try:
            # SMTP Server config + data dir
            # FIXME: Directory is hard-coded here.
            self.data_dir = params.get("data_dir", "/var/tmp/secpi/alarms")
            self.smtp_address = params["smtp_address"]
            self.smtp_port = int(params["smtp_port"])
            self.smtp_user = params["smtp_user"]
            self.smtp_pass = params["smtp_pass"]
            self.smtp_security = params["smtp_security"]
            self.unzip_attachments = str_to_value(params.get("unzip_attachments", False))
        except KeyError as ex:
            logger.error(f"Mailer: Initializing notifier failed, configuration parameter missing: {ex}")
            self.corrupted = True
            return
        except ValueError as ve:  # if one configuration parameter can't be parsed as int
            logger.error("Mailer: Wasn't able to initialize the notifier, please check your configuration: %s" % ve)
            self.corrupted = True
            return

        logger.info("Mailer: Notifier initialized")

    def notify(self, info):
        logger.info("Notifying via SMTP email")
        if not self.corrupted:
            # Mail setup
            self.message = MIMEMultipart()
            self.message["From"] = self.params["sender"]
            self.message["To"] = self.params["recipient"]
            self.message["Subject"] = self.params.get("subject", "SecPi Alarm")
            self.message.attach(
                MIMEText(
                    self.params.get("text", "Your SecPi raised an alarm. Please check the attached files."),
                    "plain",
                    "utf-8",
                )
            )
            info_str = "Recieved alarm on sensor %s from worker %s: %s" % (
                info["sensor"],
                info["worker"],
                info["message"],
            )
            self.message.attach(MIMEText(info_str, "plain"))

            try:
                self.prepare_mail_attachments()
            except:
                logger.exception("Failed to prepare email attachments")

            if self.smtp_security == "STARTTLS":
                self.send_mail_starttls()
            elif self.smtp_security == "SSL":
                self.send_mail_ssl()
            elif self.smtp_security == "NOSSL":
                self.send_mail_nossl()
            elif self.smtp_security == "NOAUTH_NOSSL":
                self.send_mail_noauth_nossl()
            elif self.smtp_security == "NOAUTH_SSL":
                self.send_mail_noauth_ssl()
            elif self.smtp_security == "NOAUTH_STARTTLS":
                self.send_mail_noauth_starttls()
        else:
            logger.error("Mailer: Wasn't able to notify because there was an initialization error")

    # Search for the latest alarm folder and attach all files within it to the mail
    def prepare_mail_attachments(self):
        # first find the latest alarm folder
        subdirs = []
        for directory in os.listdir(self.data_dir):
            full_path = os.path.join(self.data_dir, directory)
            if os.path.isdir(full_path):
                subdirs.append(full_path)
        # TODO: check if subdirs is empty
        latest_subdir = max(subdirs, key=os.path.getmtime)
        logger.debug("Mailer: Will look into %s for data" % latest_subdir)
        # then iterate through it and attach all the files to the mail
        for file in os.listdir(latest_subdir):
            filepath = "%s/%s" % (latest_subdir, file)
            # check if it really is a file
            if os.path.isfile(filepath):

                # Add each file in zipfile as separate attachment
                if self.unzip_attachments and file.endswith(".zip"):
                    self.prepare_expand_zip_attachment(filepath)

                # Add file as a whole (default)
                else:
                    with open(filepath, "rb") as f:
                        self.prepare_add_attachment(file, f.read())

            else:
                logger.debug("Mailer: %s is not a file" % file)
        # TODO: maybe log something if there are no files?

    def prepare_add_attachment(self, filename, payload):
        """Add single attachment to current mail message"""

        # Determine content type
        ctype, encoding = mimetypes.guess_type(filename, strict=False)
        maintype, subtype = ctype.split("/", 1)

        # Create proper MIME part by maintype
        if maintype == "application" and subtype in ["xml", "json"]:
            mimepart = MIMENonMultipart(maintype, subtype, charset="utf-8")
            mimepart.set_payload(payload.encode("utf-8"), "utf-8")

        elif maintype == "text":
            mimepart = MIMEText(payload.encode("utf-8"), _subtype=subtype, _charset="utf-8")

        elif maintype == "image":
            mimepart = MIMEImage(payload, _subtype=subtype)

        elif maintype == "audio":
            mimepart = MIMEAudio(payload, _subtype=subtype)

        else:
            # Encode the payload using Base64 (Content-Transfer-Encoding)
            mimepart = MIMEApplication(payload)

        # Attach MIME part to message
        mimepart.add_header("Content-Disposition", 'attachment; filename="%s"' % filename)
        self.message.attach(mimepart)

        logger.debug("Mailer: Attached file '%s' to message" % filename)

    def prepare_expand_zip_attachment(self, filepath):
        """Decode zip file and add each containing file as attachment to current mail message"""
        logger.debug("Mailer: Decoding zip file '%s' as requested" % filepath)
        import zipfile

        with zipfile.ZipFile(filepath) as zip:
            filenames = zip.namelist()

            for filename in filenames:
                payload = zip.read(filename)
                self.prepare_add_attachment(filename, payload)

    def send_mail_starttls(self):
        logger.debug("Mailer: Trying to send mail with STARTTLS")
        try:
            logger.debug("Mailer: Establishing connection to SMTP server")
            smtp = smtplib.SMTP(self.smtp_address, self.smtp_port)
            smtp.ehlo()
            smtp.starttls()
            logger.debug("Mailer: Logging in")
            smtp.login(self.smtp_user, self.smtp_pass)
            smtp.sendmail(self.message["From"], self.message["To"].split(","), self.message.as_string())
            logger.info("Mailer: Mail sent")
            smtp.quit()
        except Exception:
            logger.exception("Mailer: Unexpected error")

    def send_mail_ssl(self):
        logger.debug("Mailer: Trying to send mail with SSL")
        try:
            logger.debug("Mailer: Establishing connection to SMTP server")
            smtp = smtplib.SMTP_SSL(self.smtp_address, self.smtp_port)
            smtp.ehlo()
            logger.debug("Mailer: Logging in")
            smtp.login(self.smtp_user, self.smtp_pass)
            smtp.sendmail(self.message["From"], self.message["To"].split(","), self.message.as_string())
            logger.info("Mailer: Mail sent")
            smtp.quit()
        except Exception:
            logger.exception("Mailer: Unexpected error")

    def send_mail_nossl(self):
        logger.debug("Mailer: Trying to send mail without SSL")
        try:
            logger.debug("Mailer: Establishing connection to SMTP server")
            smtp = smtplib.SMTP(self.smtp_address, self.smtp_port)
            smtp.ehlo()
            logger.debug("Mailer: Logging in")
            smtp.login(self.smtp_user, self.smtp_pass)
            smtp.sendmail(self.message["From"], self.message["To"].split(","), self.message.as_string())
            logger.info("Mailer: Mail sent")
            smtp.quit()
        except Exception:
            logger.exception("Mailer: Unexpected error")

    def send_mail_noauth_nossl(self):
        logger.debug("Mailer: Trying to send mail without authentication")
        try:
            logger.debug("Mailer: Establishing connection to SMTP server")
            smtp = smtplib.SMTP(self.smtp_address, self.smtp_port)
            smtp.ehlo()
            smtp.sendmail(self.message["From"], self.message["To"].split(","), self.message.as_string())
            logger.info("Mailer: Mail sent")
            smtp.quit()
        except Exception:
            logger.exception("Mailer: Unexpected error")

    def send_mail_noauth_ssl(self):
        logger.debug("Mailer: Trying to send mail without authentication")
        try:
            logger.debug("Mailer: Establishing connection to SMTP server")
            smtp = smtplib.SMTP_SSL(self.smtp_address, self.smtp_port)
            smtp.ehlo()
            smtp.sendmail(self.message["From"], self.message["To"].split(","), self.message.as_string())
            logger.info("Mailer: Mail sent")
            smtp.quit()
        except Exception:
            logger.exception("Mailer: Unexpected error")

    def send_mail_noauth_starttls(self):
        logger.debug("Mailer: Trying to send mail with STARTTLS")
        try:
            logger.debug("Mailer: Establishing connection to SMTP server")
            smtp = smtplib.SMTP(self.smtp_address, self.smtp_port)
            smtp.ehlo()
            smtp.starttls()
            smtp.sendmail(self.message["From"], self.message["To"].split(","), self.message.as_string())
            logger.info("Mailer: Mail sent")
            smtp.quit()
        except Exception:
            logger.exception("Mailer: Unexpected error")

    def cleanup(self):
        logger.debug("Mailer: No cleanup necessary at the moment")

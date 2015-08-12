import logging
import os
import smtplib

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class Mailer:

	def __init__(self, sender, recipient, subject, text, data_dir,
				 smtp_address, smtp_port, smtp_user, smtp_pass, smtp_security):
		logging.basicConfig(format='%(asctime)s | %(levelname)s:  %(message)s', level=logging.DEBUG)

		# Mail setup
		self.message = MIMEMultipart()
		self.message["From"] = sender
		self.message["To"] = recipient
		self.message["Subject"] = subject
		self.message.attach(MIMEText(text, "plain"))
		
		# SMTP Server config + data dir
		self.data_dir = data_dir
		self.smtp_address = smtp_address
		self.smtp_port = smtp_port
		self.smtp_user = smtp_user
		self.smtp_pass = smtp_pass
		self.smtp_security = smtp_security # not used yet

		logging.info("Mailer initialized")
		
	# TODO: include more details about which sensors signaled, etc.???
	def send_mail(self):
		if self.smtp_security == "STARTTLS":
			self.send_mail_starttls()
		elif self.smtp_security == "SSL":
			self.send_mail_ssl()
		elif self.smtp_security == "NOSSL":
			self.send_mail_nossl()
		elif self.smtp_security == "NOAUTH":
			self.send_mail_noauth()

	def prepare_mail_attachments(self):
		for file in os.listdir(self.data_dir): # iterate through files and attach them to the mail
			# check if it really is a file
			if os.path.isfile("%s/%s" % (self.data_dir, file)):
				f = open("%s/%s" % (self.data_dir, file), "rb")
				att = MIMEApplication(f.read())
				att.add_header('Content-Disposition','attachment; filename="%s"' % file)
				f.close()
				self.message.attach(att)
				logging.debug("Attached file '%s' to message" % file)
			else:
				logging.debug("%s is not a file" % file)

	def send_mail_starttls(self):
		self.prepare_mail_attachments()
		print "sending starttls"
		try:
			logging.debug("Establishing connection to SMTP server...")
			smtp = smtplib.SMTP(self.smtp_address, self.smtp_port)
			smtp.ehlo()
			smtp.starttls()
			smtp.login(self.smtp_user, self.smtp_pass)
			smtp.sendmail(self.message["From"], self.message["To"], self.message.as_string())
			logging.info("Mail sent")
			smtp.quit()
		except Exception, e:
			print(e)

	def send_mail_ssl(self):
		self.prepare_mail_attachments()
		print "send mail ssl"

	def send_mail_nossl(self):
		self.prepare_mail_attachments()
		print "send mail no ssl"

	def send_mail_noauth(self):
		self.prepare_mail_attachments()
		print "noauth"





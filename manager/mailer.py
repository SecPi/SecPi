import logging
import os
import smtplib

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tools.notifier import Notifier

class Mailer(Notifier):

	def __init__(self, id, params):
		super(Mailer, self).__init__(id, params)
		logging.basicConfig(format='%(asctime)s | %(levelname)s:  %(message)s', level=logging.DEBUG)
		
		# SMTP Server config + data dir
		self.data_dir = params["data_dir"]
		self.smtp_address = params["smtp_address"]
		self.smtp_port = int(params["smtp_port"])
		self.smtp_user = params["smtp_user"]
		self.smtp_pass = params["smtp_pass"]
		self.smtp_security = params["smtp_security"]

		logging.info("Mailer initialized")
	
	def notify(self, info):
		# Mail setup
		self.message = MIMEMultipart()
		self.message["From"] = params["sender"]
		self.message["To"] = params["recipient"]
		self.message["Subject"] = params["subject"]
		self.message.attach(MIMEText(params["text"], "plain"))
		info_str = "Recieved alarm on sensor %s from worker %s: %s"%(info['sensor'], info['worker'], info['message'])
		self.message.attach(MIMEText(info_str, "plain"))
		
		self.prepare_mail_attachments()
		
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
		logging.debug("Will look into %s for data" % latest_subdir)
		#then iterate through it and attach all the files to the mail
		for file in os.listdir(latest_subdir):
			# check if it really is a file
			if os.path.isfile("%s/%s" % (latest_subdir, file)):
				f = open("%s/%s" % (latest_subdir, file), "rb")
				att = MIMEApplication(f.read())
				att.add_header('Content-Disposition','attachment; filename="%s"' % file)
				f.close()
				self.message.attach(att)
				logging.debug("Attached file '%s' to message" % file)
			else:
				logging.debug("%s is not a file" % file)
		# TODO: maybe log something if there are no files?

	def send_mail_starttls(self):
		logging.debug("Trying to send mail with STARTTLS")
		try:
			logging.debug("Establishing connection to SMTP server...")
			smtp = smtplib.SMTP(self.smtp_address, self.smtp_port)
			smtp.ehlo()
			smtp.starttls()
			logging.debug("Logging in...")
			smtp.login(self.smtp_user, self.smtp_pass)
			smtp.sendmail(self.message["From"], self.message["To"], self.message.as_string())
			logging.info("Mail sent")
			smtp.quit()
		except Exception, e:
			logging.error(e)

	def send_mail_ssl(self):
		logging.debug("Trying to send mail with SSL")
		try:
			logging.debug("Establishing connection to SMTP server...")
			smtp = smtplib.SMTP_SSL(self.smtp_address, self.smtp_port)
			smtp.ehlo()
			logging.debug("Logging in...")
			smtp.login(self.smtp_user, self.smtp_pass)
			smtp.sendmail(self.message["From"], self.message["To"], self.message.as_string())
			logging.info("Mail sent")
			smtp.quit()
		except Exception, e:
			logging.error(e)

	def send_mail_nossl(self):
		logging.debug("Trying to send mail without SSL")
		try:
			logging.debug("Establishing connection to SMTP server...")
			smtp = smtplib.SMTP(self.smtp_address, self.smtp_port)
			smtp.ehlo()
			logging.debug("Logging in...")
			smtp.login(self.smtp_user, self.smtp_pass)
			smtp.sendmail(self.message["From"], self.message["To"], self.message.as_string())
			logging.info("Mail sent")
			smtp.quit()
		except Exception, e:
			logging.error(e)

	def send_mail_noauth_nossl(self):
		logging.debug("Trying to send mail without authentication")
		try:
			logging.debug("Establishing connection to SMTP server...")
			smtp = smtplib.SMTP(self.smtp_address, self.smtp_port)
			smtp.ehlo()
			smtp.sendmail(self.message["From"], self.message["To"], self.message.as_string())
			logging.info("Mail sent")
			smtp.quit()
		except Exception, e:
			logging.error(e)
	
	def send_mail_noauth_ssl(self):
		logging.debug("Trying to send mail without authentication")
		try:
			logging.debug("Establishing connection to SMTP server...")
			smtp = smtplib.SMTP_SSL(self.smtp_address, self.smtp_port)
			smtp.ehlo()
			smtp.sendmail(self.message["From"], self.message["To"], self.message.as_string())
			logging.info("Mail sent")
			smtp.quit()
		except Exception, e:
			logging.error(e)
	
	def send_mail_noauth_starttls(self):
		logging.debug("Trying to send mail with STARTTLS")
		try:
			logging.debug("Establishing connection to SMTP server...")
			smtp = smtplib.SMTP(self.smtp_address, self.smtp_port)
			smtp.ehlo()
			smtp.starttls()
			smtp.sendmail(self.message["From"], self.message["To"], self.message.as_string())
			logging.info("Mail sent")
			smtp.quit()
		except Exception, e:
			logging.error(e)




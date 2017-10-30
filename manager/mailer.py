import logging
import os
import smtplib

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tools.notifier import Notifier
from tools.utils import str_to_value

class Mailer(Notifier):

	def __init__(self, id, params):
		super(Mailer, self).__init__(id, params)
		
		try:
			# SMTP Server config + data dir
			self.data_dir = params.get("data_dir", "/var/tmp/secpi/alarms")
			self.smtp_address = params["smtp_address"]
			self.smtp_port = int(params["smtp_port"])
			self.smtp_user = params["smtp_user"]
			self.smtp_pass = params["smtp_pass"]
			self.smtp_security = params["smtp_security"]
			self.unzip_attachments = str_to_value(params.get("unzip_attachments", False))
		except KeyError as ke: # if config parameters are missing
			logging.error("Mailer: Wasn't able to initialize the notifier, it seems there is a config parameter missing: %s" % ke)
			self.corrupted = True
			return
		except ValueError as ve: # if one configuration parameter can't be parsed as int
			logging.error("Mailer: Wasn't able to initialize the notifier, please check your configuration: %s" % ve)
			self.corrupted = True
			return

		logging.info("Mailer: Notifier initialized")
	
	def notify(self, info):
		if not self.corrupted:
			# Mail setup
			self.message = MIMEMultipart()
			self.message["From"] = self.params["sender"]
			self.message["To"] = self.params["recipient"]
			self.message["Subject"] = self.params.get("subject", "SecPi Alarm")
			self.message.attach(MIMEText(self.params.get("text", "Your SecPi raised an alarm. Please check the attached files."), "plain", 'utf-8'))
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
		else:
			logging.error("Mailer: Wasn't able to notify because there was an initialization error")
		

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
		logging.debug("Mailer: Will look into %s for data" % latest_subdir)
		#then iterate through it and attach all the files to the mail
		for file in os.listdir(latest_subdir):
			filepath = "%s/%s" % (latest_subdir, file)
			# check if it really is a file
			if os.path.isfile(filepath):

				# Add each file in zipfile as separate attachment
				if self.unzip_attachments and file.endswith('.zip'):
					self.prepare_expand_zip_attachment(filepath)

				# Add file as a whole (default)
				else:
					with open(filepath, "rb") as f:
						self.prepare_add_attachment(file, f.read())

			else:
				logging.debug("Mailer: %s is not a file" % file)
		# TODO: maybe log something if there are no files?

	def prepare_add_attachment(self, filename, content):
		"""Add single attachment to current mail message"""
		att = MIMEApplication(content)
		att.add_header('Content-Disposition','attachment; filename="%s"' % filename)
		self.message.attach(att)
		logging.debug("Mailer: Attached file '%s' to message" % filename)

	def prepare_expand_zip_attachment(self, filepath):
		"""Decode zip file and add each containing file as attachment to current mail message"""
		logging.debug("Mailer: Decoding zip file '%s' as requested" % filepath)
		import zipfile
		with zipfile.ZipFile(filepath) as zip:
			filenames = zip.namelist()

			for filename in filenames:
				payload = zip.read(filename)
				self.prepare_add_attachment(filename, payload)

	def send_mail_starttls(self):
		logging.debug("Mailer: Trying to send mail with STARTTLS")
		try:
			logging.debug("Mailer: Establishing connection to SMTP server...")
			smtp = smtplib.SMTP(self.smtp_address, self.smtp_port)
			smtp.ehlo()
			smtp.starttls()
			logging.debug("Mailer: Logging in...")
			smtp.login(self.smtp_user, self.smtp_pass)
			smtp.sendmail(self.message["From"], self.message["To"].split(','), self.message.as_string())
			logging.info("Mailer: Mail sent")
			smtp.quit()
		except Exception as e:
			logging.error("Mailer: Unknown error: %s" % e)

	def send_mail_ssl(self):
		logging.debug("Mailer: Trying to send mail with SSL")
		try:
			logging.debug("Mailer: Establishing connection to SMTP server...")
			smtp = smtplib.SMTP_SSL(self.smtp_address, self.smtp_port)
			smtp.ehlo()
			logging.debug("Mailer: Logging in...")
			smtp.login(self.smtp_user, self.smtp_pass)
			smtp.sendmail(self.message["From"], self.message["To"].split(','), self.message.as_string())
			logging.info("Mailer: Mail sent")
			smtp.quit()
		except Exception as e:
			logging.error("Mailer: Unknown error: %s" % e)

	def send_mail_nossl(self):
		logging.debug("Mailer: Trying to send mail without SSL")
		try:
			logging.debug("Mailer: Establishing connection to SMTP server...")
			smtp = smtplib.SMTP(self.smtp_address, self.smtp_port)
			smtp.ehlo()
			logging.debug("Mailer: Logging in...")
			smtp.login(self.smtp_user, self.smtp_pass)
			smtp.sendmail(self.message["From"], self.message["To"].split(','), self.message.as_string())
			logging.info("Mailer: Mail sent")
			smtp.quit()
		except Exception as e:
			logging.error("Mailer: Unknown error: %s" % e)

	def send_mail_noauth_nossl(self):
		logging.debug("Mailer: Trying to send mail without authentication")
		try:
			logging.debug("Mailer: Establishing connection to SMTP server...")
			smtp = smtplib.SMTP(self.smtp_address, self.smtp_port)
			smtp.ehlo()
			smtp.sendmail(self.message["From"], self.message["To"].split(','), self.message.as_string())
			logging.info("Mailer: Mail sent")
			smtp.quit()
		except Exception as e:
			logging.error("Mailer: Unknown error: %s" % e)
	
	def send_mail_noauth_ssl(self):
		logging.debug("Mailer: Trying to send mail without authentication")
		try:
			logging.debug("Mailer: Establishing connection to SMTP server...")
			smtp = smtplib.SMTP_SSL(self.smtp_address, self.smtp_port)
			smtp.ehlo()
			smtp.sendmail(self.message["From"], self.message["To"].split(','), self.message.as_string())
			logging.info("Mailer: Mail sent")
			smtp.quit()
		except Exception as e:
			logging.error("Mailer: Unknown error: %s" % e)
	
	def send_mail_noauth_starttls(self):
		logging.debug("Mailer: Trying to send mail with STARTTLS")
		try:
			logging.debug("Mailer: Establishing connection to SMTP server...")
			smtp = smtplib.SMTP(self.smtp_address, self.smtp_port)
			smtp.ehlo()
			smtp.starttls()
			smtp.sendmail(self.message["From"], self.message["To"].split(','), self.message.as_string())
			logging.info("Mailer: Mail sent")
			smtp.quit()
		except Exception as e:
			logging.error("Mailer: Unknown error: %s" % e)

	def cleanup(self):
		logging.debug("Mailer: No cleanup necessary at the moment")


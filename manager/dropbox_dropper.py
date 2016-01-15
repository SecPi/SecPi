import dropbox
import logging
import os

from tools.notifier import Notifier

class Dropbox_Dropper(Notifier):

	def __init__(self, id, params):
		super(Dropbox_Dropper, self).__init__(id, params)
		try:
			self.access_token = params["access_token"]
		except KeyError, k:
			logging.error("Dropxbox: Error while trying to initialize notifier, it seems there is a config parameter missing: %s" % k)
			self.corrupted = True
			return

		try:
			self.dbx = dropbox.Dropbox(self.access_token)
		except Exception, e:
			logging.error("Dropbox: Error while connecting to Dropbox service: %s" % e)
			self.corrupted = True
			return

		self.data_dir = "/var/tmp/secpi/alarms/" #change this maybe?

		logging.info("Dropbox initialized")


	def notify(self, info):
		if not self.corrupted:
			#info_str = "Recieved alarm on sensor %s from worker %s: %s"%(info['sensor'], info['worker'], info['message'])
			latest_subdir = self.get_latest_subdir()

			dropbox_dir = "/%s" % latest_subdir.split("/")[-1] #pfui
			#self.dbx.files_create_folder(dropbox_dir) # shouldn't be necessary, automatically created 
			for file in os.listdir(latest_subdir):
				if os.path.isfile("%s/%s" % (latest_subdir, file)):
					f = open("%s/%s" % (latest_subdir, file), "rb")
					data = f.read()
					try:
						logging.info("Dropbox: Trying to upload file %s to %s" % (file, dropbox_dir))
						res = self.dbx.files_upload(data, "%s/%s" % (dropbox_dir, file))
					except dropbox.exceptions.ApiError as d:
						logging.error("Dropbox: API error: %s" % d)
					f.close()
			logging.info("Dropbox: Upload succeeded")
		else:
			logging.error("Dropbox: Wasn't able to notify because there was an initialization error")


	def get_latest_subdir(self):
		subdirs = []
		for directory in os.listdir(self.data_dir):
			full_path = os.path.join(self.data_dir, directory)
			if os.path.isdir(full_path):
				subdirs.append(full_path)
		# TODO: check if subdirs is empty
		latest_subdir = max(subdirs, key=os.path.getmtime)
		return latest_subdir

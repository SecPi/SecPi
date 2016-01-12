import dropbox
import logging
import os

from tools.notifier import Notifier

class Dropbox_Dropper(Notifier):

	def __init__(self, id, params):
		super(Dropbox_Dropper, self).__init__(id, params)
		self.access_token = params["access_token"]
		self.dbx = dropbox.Dropbox(self.access_token)
		self.data_dir = "/var/tmp/secpi/alarms/" #change this maybe?

		logging.info("Dropbox initialized")


	def notify(self, info):
		info_str = "Recieved alarm on sensor %s from worker %s: %s"%(info['sensor'], info['worker'], info['message'])
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


	def get_latest_subdir(self):
		subdirs = []
		for directory in os.listdir(self.data_dir):
			full_path = os.path.join(self.data_dir, directory)
			if os.path.isdir(full_path):
				subdirs.append(full_path)
		# TODO: check if subdirs is empty
		latest_subdir = max(subdirs, key=os.path.getmtime)
		return latest_subdir

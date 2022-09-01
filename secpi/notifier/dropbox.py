import logging
import os

import dropbox as dropbox_lib

from secpi.model.notifier import Notifier

logger = logging.getLogger(__name__)


class DropboxFileUpload(Notifier):
    def __init__(self, id, params):

        super(DropboxFileUpload, self).__init__(id, params)
        try:
            self.access_token = params["access_token"]
        except KeyError as ex:
            logger.error(f"DropboxFileUpload: Initializing notifier failed, configuration parameter missing: {ex}")
            self.corrupted = True
            return

        try:
            self.dbx = dropbox_lib.Dropbox(self.access_token)
        except Exception:
            logger.exception("Connecting to DropboxFileUpload failed")
            self.corrupted = True
            return

        # FIXME: Directory is hard-coded here.
        self.data_dir = "/var/tmp/secpi/alarms/"

        logger.info("DropboxFileUpload initialized")

    def notify(self, info):
        if not self.corrupted:

            # info_str = "Received alarm on sensor %s from worker %s: %s" % (
            #    info["sensor"],
            #    info["worker"],
            #    info["message"],
            # )

            latest_subdir = self.get_latest_subdir()

            dropbox_dir = "/%s" % latest_subdir.split("/")[-1]  # pfui
            # self.dbx.files_create_folder(dropbox_dir) # shouldn't be necessary, automatically created
            for file in os.listdir(latest_subdir):
                if os.path.isfile("%s/%s" % (latest_subdir, file)):
                    with open("%s/%s" % (latest_subdir, file), "rb") as f:
                        data = f.read()

                    try:
                        logger.info("DropboxFileUpload: Trying to upload file %s to %s" % (file, dropbox_dir))
                        res = self.dbx.files_upload(data, "%s/%s" % (dropbox_dir, file))
                        logger.info("DropboxFileUpload: Upload of file %s succeeded" % file)
                    except dropbox_lib.exceptions.ApiError as d:
                        logger.error("DropboxFileUpload: API error: %s" % d)
                    except Exception as e:  # currently this catches wrong authorization, we should change this
                        logger.error("DropboxFileUpload: Wasn't able to upload file: %s" % e)
        else:
            logger.error("DropboxFileUpload: Wasn't able to notify because there was an initialization error")

    def get_latest_subdir(self):
        subdirs = []
        for directory in os.listdir(self.data_dir):
            full_path = os.path.join(self.data_dir, directory)
            if os.path.isdir(full_path):
                subdirs.append(full_path)
        # TODO: check if subdirs is empty
        latest_subdir = max(subdirs, key=os.path.getmtime)
        return latest_subdir

    def cleanup(self):
        logger.debug("DropboxFileUpload: No cleanup necessary at the moment")

import logging

import dropbox as dropbox_lib

from secpi.model.message import NotificationMessage
from secpi.model.notifier import Notifier

logger = logging.getLogger(__name__)


class DropboxFileUpload(Notifier):
    def __init__(self, id, params):

        super(DropboxFileUpload, self).__init__(id, params)
        try:
            self.access_token = params["access_token"]
            self.path = params.get("path", "")
            if not self.path.startswith("/"):
                self.path = f"/{self.path}"
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

        logger.info("DropboxFileUpload initialized")

    def notify(self, info: NotificationMessage):
        if not self.corrupted:

            # Render the notification message.
            # info_str = info.render_message()

            filename = f"{info.attachment_name}.zip"
            filepath = f"{self.path}/{filename}"

            try:
                logger.info(f"DropboxFileUpload: Uploading file {filename} to {self.path}")
                # TODO: Where to report successful outcome?
                _ = self.dbx.files_upload(info.payload, filepath)
                logger.info(f"DropboxFileUpload: Upload of file {filename} succeeded")
            except Exception:
                logger.exception("DropboxFileUpload: Uploading file failed")

        else:
            logger.error("DropboxFileUpload: Notify failed because there was an initialization error")

    def cleanup(self):
        logger.debug("DropboxFileUpload: No cleanup necessary at the moment")

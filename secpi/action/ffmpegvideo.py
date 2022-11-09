import logging
import tempfile
import time
from pathlib import Path

import ffmpy

from secpi.model.action import Action, ActionResponse, FileResponse

logger = logging.getLogger(__name__)


class FFMPEGVideo(Action):
    """
    This module is like the "webcam" module but uses the fine "ffmpeg" for capturing picture snapshots.
    For interacting with ffmpeg, the ffmpy command line wrapper is used.

    Setup:
            - apt install ffmpeg
            - pip install ffmpy
    """

    DEBUG_FFMPEG_OUTPUT = True

    def __init__(self, identifier, params, worker):
        super().__init__(identifier, params, worker)

        logger.info("FFMPEGVideo: Initializing")

        # Set parameter defaults
        self.params.setdefault("name", "default")
        self.params.setdefault("count", 1)
        self.params.setdefault("interval", 2)
        self.params.setdefault("ffmpeg_global_options", "-v quiet -stats")
        self.params.setdefault("ffmpeg_input_options", None)
        self.params.setdefault("ffmpeg_output_options", "-pix_fmt yuvj420p -vsync 2 -vframes 1")

        # Define required params
        required_params = ["url"]

        # Configuration parameter checks
        for required_param in required_params:
            if required_param not in self.params:
                self.post_err(f"FFMPEGVideo: Configuration parameter '{required_param}' is missing")
                self.corrupted = True
                return

    def exffmpeg(self, url, filename, global_options=None, input_options=None, output_options=None):
        """
        Run capturing with `ffmpeg`.
        """
        ff = ffmpy.FFmpeg(
            global_options=global_options, inputs={url: input_options}, outputs={filename: output_options}
        )
        return ff.run()

    def take_adv_picture(self, num_of_pic, seconds_between):
        """
        Take a series of pictures within a given interval.
        """
        logger.debug("FFMPEGVideo: Starting to capture images")

        name = self.params["name"]
        url = self.params["url"]

        response = ActionResponse()
        with tempfile.TemporaryDirectory() as tmpdir:
            logger.info(f"FFMPEGVideo: Capturing images to {tmpdir}")
            filepaths = []
            for index in range(0, num_of_pic):
                timestamp = time.strftime("%Y%m%dT%H%M%S")
                filename = f"{name}-{timestamp}-{index}.jpg"
                filepath = Path(tmpdir).joinpath(filename)
                logger.info(f"FFMPEGVideo: Capturing picture from {url} to {filename}")
                try:
                    result = self.exffmpeg(
                        url,
                        filepath,
                        global_options=self.params["ffmpeg_global_options"],
                        input_options=self.params["ffmpeg_input_options"],
                        output_options=self.params["ffmpeg_output_options"],
                    )
                    if self.DEBUG_FFMPEG_OUTPUT:
                        logger.debug(f"FFMPEGVideo: output: {result}")
                    filepaths.append(filepath)

                except Exception as ex:
                    message = f"FFMPEGVideo: Failed capturing image from {url} to {filename}"
                    logger.exception(message)
                    self.post_err(f"{message}: {ex}")

                # Wait until next interval.
                time.sleep(seconds_between)

            for item in Path(tmpdir).iterdir():
                with open(item, "rb") as f:
                    response.add(FileResponse(name=item.name, payload=f.read()))

        logger.debug("FFMPEGVideo: Finished capturing images")
        return response

    def execute(self):
        if not self.corrupted:
            self.take_adv_picture(int(self.params["count"]), int(self.params["interval"]))
        else:
            self.post_err("FFMPEGVideo: Failed capturing because of an initialization error")

    def cleanup(self):
        logger.debug("FFMPEGVideo: No cleanup necessary at the moment")

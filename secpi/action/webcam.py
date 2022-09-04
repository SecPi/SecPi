import logging
import time

import pygame.camera
import pygame.image

from secpi.model.action import Action, ActionResponse, FileResponse

logger = logging.getLogger(__name__)


class Webcam(Action):
    def __init__(self, id, params, worker):
        super(Webcam, self).__init__(id, params, worker)

        try:
            self.path = params["path"]
            self.resolution = (int(params["resolution_x"]), int(params["resolution_y"]))
        except ValueError as ve:  # if resolution can't be parsed as int
            self.post_err("Webcam: Wasn't able to initialize the device, please check your configuration: %s" % ve)
            self.corrupted = True
            return
        except KeyError as ke:  # if config parameters are missing in file
            self.post_err(
                "Webcam: Wasn't able to initialize the device, it seems there is a config parameter missing: %s" % ke
            )
            self.corrupted = True
            return

        pygame.camera.init()
        self.cam = pygame.camera.Camera(self.path, self.resolution)
        logger.debug("Webcam: Video device initialized: %s" % self.path)

    # take a series of pictures within a given interval
    def take_adv_picture(self, num_of_pic, seconds_between):
        logger.debug("Webcam: Trying to take pictures")
        try:
            self.cam.start()
        except SystemError as se:  # device path wrong
            logger.exception("Starting webcam failed")
            self.post_err("Webcam: Wasn't able to find video device at device path: %s" % self.path)
            return
        except AttributeError as ae:  # init failed, taking pictures won't work -> shouldn't happen but anyway
            logger.exception("Starting webcam failed")
            self.post_err("Webcam: Couldn't take pictures because video device wasn't initialized properly")
            return

        response = ActionResponse()
        try:
            for index in range(0, num_of_pic):

                img = self.cam.get_image()
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{index}.jpg"
                response.add(FileResponse(name=filename, payload=pygame.image.tostring(img, "RGBA")))

                time.sleep(seconds_between)

        except Exception as ex:
            logger.exception("Webcam: Failed taking pictures")
            self.post_err(f"Webcam: Failed taking pictures: {ex}")

        try:
            self.cam.stop()
        except:
            logger.exception("Stopping Webcam failed")

        logger.debug("Webcam: Finished taking pictures")
        return response

    def execute(self):
        if not self.corrupted:
            return self.take_adv_picture(int(self.params["count"]), int(self.params["interval"]))
        else:
            self.post_err("Webcam: Wasn't able to take pictures because of an initialization error")

    def cleanup(self):
        logger.debug("Webcam: No cleanup necessary at the moment")

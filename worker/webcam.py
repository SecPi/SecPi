import pygame.camera
import pygame.image
import time

class Webcam:

	def __init__(self, path, resolution):
		self.path = path
		self.resolution = resolution
		pygame.camera.init()
		self.cam = pygame.camera.Camera(path, resolution)

	def take_picture(self):
		self.cam.start()
		img = self.cam.get_image()
		pygame.image.save(img, "%s.jpg" % time.strftime("%Y%m%d_%H%M%S"))
		self.cam.stop()

	def take_adv_picture(self, num_of_pic, seconds_between):
		self.cam.start()
		for i in range(0,num_of_pic):
			img = self.cam.get_image()
			pygame.image.save(img, "%s_%d.jpg" % (time.strftime("%Y%m%d_%H%M%S"), i))
			time.sleep(seconds_between)
		self.cam.stop()


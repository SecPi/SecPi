import pygame.camera
import pygame.image
import time
import logging

from tools.action import Action

class Webcam(Action):

	def __init__(self, id, params):
		logging.basicConfig(format='%(asctime)s | %(levelname)s:  %(message)s', level=logging.INFO)	# TODO make it nicer
		super(Webcam, self).__init__(id, params)	

		self.path = params["path"]
		self.resolution = (int(params["resolution_x"]), int(params["resolution_y"]))
		self.data_path = params["data_path"]
		pygame.camera.init()
		self.cam = pygame.camera.Camera(self.path, self.resolution)
		logging.debug("Webcam initialized")

	def take_adv_picture(self, num_of_pic, seconds_between):
		self.cam.start()
		try:
			for i in range(0,num_of_pic):
				img = self.cam.get_image()
				pygame.image.save(img, "%s/%s_%d.jpg" % (self.data_path, time.strftime("%Y%m%d_%H%M%S"), i))
				time.sleep(seconds_between)
		except:
			print("Error taking picture!")
		self.cam.stop()
	
	def execute(self):
		self.take_adv_picture(int(self.params["count"]), int(self.params["interval"]))
		
	def cleanup(self):
		print "No cleanup necessary at the moment"# do some cleanup?
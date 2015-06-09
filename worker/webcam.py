import pygame.camera
import pygame.image
import time

from tools.action import Action

class Webcam(Action):

	def __init__(self, id, params):
		super(Webcam, self).__init__(id, params)
		self.path = params["path"]
		self.resolution = (int(params["resolution_x"]), int(params["resolution_y"]))
		pygame.camera.init()
		self.cam = pygame.camera.Camera(self.path, self.resolution)

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
	
	def execute(self):
		self.take_adv_picture(int(self.params["count"]), int(self.params["interval"]))
		
		# send pictures
		# channel.basic_publish(exchange='manager', routing_key='data', body="BLOB")
		
		


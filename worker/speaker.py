import pygame
from tools.action import Action


class Speaker(Action):

	def __init__(self, id, params):
		super(Speaker, self).__init__(id, params)
		self.path_to_audio = params["path_to_audio"]
		self.repetitions = params["repetitions"] #TODO: change


	def play_audio(self):
		print "playing audio"
		pygame.mixer.init()
		pygame.mixer.music.load(self.path_to_audio)
		pygame.mixer.music.set_volume(1)

		for i in range(0, self.repetitions):
			pygame.mixer.music.rewind()
			pygame.mixer.music.play()
			while pygame.mixer.music.get_busy():
				continue
		pygame.mixer.quit()
		print "finished playing audio"

	def execute(self):
		self.play_audio()

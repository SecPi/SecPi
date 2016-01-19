import pygame
import logging

from tools.action import Action

class Speaker(Action):

	def __init__(self, id, params):
		super(Speaker, self).__init__(id, params)
		try:
			self.path_to_audio = params["path_to_audio"]
			self.repetitions = int(params["repetitions"]) #TODO: change| why did i write this??
		except ValueError as e: # if repetitions can't be parsed as int
			logging.error("Speaker: Wasn't able to initialize the device, please check your configuration: %s" % e)
			self.corrupted = True
			return
		except KeyError as k: # if config parameters are missing in file
			logging.error("Speaker: Wasn't able to initialize the device, it seems there is a config parameter missing: %s" % k)
			self.corrupted = True
			return

		logging.debug("Speaker: Audio device initialized")

	def play_audio(self):
		logging.debug("Speaker: Trying to play audio")
		pygame.mixer.init()
		try:
			pygame.mixer.music.load(self.path_to_audio)
		except Exception as e: # audio file doesn't exist or is not playable
			logging.error("Speaker: Wasn't able to load audio file: %s" % e)
			pygame.mixer.quit()
			return
		pygame.mixer.music.set_volume(1)

		for i in range(0, self.repetitions):
			pygame.mixer.music.rewind()
			pygame.mixer.music.play()
			while pygame.mixer.music.get_busy():
				continue
		pygame.mixer.quit()
		logging.debug("Speaker: Finished playing audio")

	def execute(self):
		if not self.corrupted:
			self.play_audio()
		else:
			logging.error("Speaker: Wasn't able to play sound because of an initialization error")
		
	def cleanup(self):
		logging.debug("Speaker: No cleanup necessary at the moment")		
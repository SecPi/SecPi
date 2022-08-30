import os
import time
import ffmpy
import logging

from tools.action import Action


logger = logging.getLogger(__name__)


class FFMPEGVideo(Action):
	"""
	This module is like the "webcam" module but uses the fine "ffmpeg" for capturing picture snapshots.
	For interacting with ffmpeg, the ffmpy command line wrapper is used.

	Setup:
		- apt install ffmpeg
		- pip install ffmpy
	"""

	def __init__(self, id, params, worker):
		super(FFMPEGVideo, self).__init__(id, params, worker)

		logger.info('FFMPEGVideo: Starting')

		# Set parameter defaults
		self.params.setdefault('name', 'default')
		self.params.setdefault('count', 3)
		self.params.setdefault('interval', 5)
		# FIXME: This is hardcoded.
		self.params.setdefault('data_path', '/var/tmp/secpi/worker_data')
		self.params.setdefault('ffmpeg_global_options', '-v quiet -stats')
		self.params.setdefault('ffmpeg_input_options',  None)
		self.params.setdefault('ffmpeg_output_options', '-pix_fmt yuvj420p -vsync 2 -vframes 1')

		# Define required params
		required_params = ['url']

		# Configuration parameter checks
		for required_param in required_params:
			if required_param not in self.params:
				self.post_err("FFMPEGVideo: Configuration parameter '{}' is missing".format(required_param))
				self.corrupted = True
				return

		# Sanity checks
		if not os.path.exists(self.params['data_path']):
			self.post_err("FFMPEGVideo: Path does not exist. data_path={}".format(self.params['data_path']))
			self.corrupted = True
			return

	def exffmpeg(self, url, filename, global_options=None, input_options=None, output_options=None):
		ff = ffmpy.FFmpeg(
			global_options = global_options,
			inputs  = {url: input_options},
			outputs = {filename: output_options}
		)
		ff.run()

	# Take a series of pictures within a given interval
	def take_adv_picture(self, num_of_pic, seconds_between):
		logger.debug("FFMPEGVideo: Trying to take pictures")

		name = self.params['name']
		url  = self.params['url']
		timestamp = time.strftime("%Y%m%d%H%M%S")

		for index in range(0, num_of_pic):
			filename = '{name}-{timestamp}-{index}.jpg'.format(**locals())
			filepath = os.path.join(self.params['data_path'], filename)
			logger.info("FFMPEGVideo: Trying to take a picture from {url} to {filepath}".format(**locals()))
			try:
				result = self.exffmpeg(url, filepath,
					global_options=self.params['ffmpeg_global_options'],
					input_options=self.params['ffmpeg_input_options'],
					output_options=self.params['ffmpeg_output_options'],
				)
			except Exception as ex:
				self.post_err("FFMPEGVideo: Wasn't able to take picture from {url} to {filepath}: %s".format(**locals()) % ex)

			# Wait until next interval
			time.sleep(seconds_between)

		logger.debug("FFMPEGVideo: Finished taking pictures")


	def execute(self):
		if not self.corrupted:
			self.take_adv_picture(int(self.params["count"]), int(self.params["interval"]))
		else:
			self.post_err("FFMPEGVideo: Wasn't able to take pictures because of an initialization error")

	def cleanup(self):
		logger.debug("FFMPEGVideo: No cleanup necessary at the moment")

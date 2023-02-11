import os


class File:
	# Google drive ID
	id = None
	name = None
	mimeType = None
	extension = None
	metadata = {}
	encrypted = None
	refresh_metadata = None
	# type = video/fanart/subtitles
	# compatible_name = self.fileOperations.removeProhibitedFSchars(name)
	# contents = None
	# path = None

	def removeFileExtension(self):
		return os.path.splitext(self.name)[0]

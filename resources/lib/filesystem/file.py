import os


class File:
	id = None
	name = None
	basename = None
	type = None
	extension = None
	encrypted = None
	modifiedTime = None

	def removeFileExtension(self):
		self.basename = os.path.splitext(self.name)[0]

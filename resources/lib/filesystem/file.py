import os


class File:
	id = None
	name = None
	type = None
	extension = None
	encrypted = None
	modifiedTime = None

	@property
	def basename(self):
		return os.path.splitext(self.name)[0]

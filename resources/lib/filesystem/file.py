import os


class File:

	def __init__(self):
		self.id = None
		self.type = None
		self.remoteName = None
		self.localName = None
		self.localPath = None
		self.extension = None
		self.encryptionID = None
		self.modifiedTime = None
		self.updateDB = False
		self.original = True

	@property
	def basename(self):
		return os.path.splitext(self.remoteName)[0]

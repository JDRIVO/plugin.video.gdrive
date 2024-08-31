from . import helpers


class Folder:

	def __init__(self, id, parentID, name, remotePath, localPath, modifiedTime=None):
		self.id = id
		self.parentID = parentID
		self.name = name
		self.remotePath = remotePath
		self.localPath = localPath
		self.processingPath = None
		self.modifiedTime = helpers.convertTime(modifiedTime) if modifiedTime else None
		self.files = {
			"strm": [],
			"video": [],
			"media_assets": {},
		}

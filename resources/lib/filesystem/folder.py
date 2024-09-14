from helpers import rfcToTimestamp


class Folder:

	def __init__(self, id, parentID, name, remotePath, localPath, modifiedTime=None):
		self.id = id
		self.parentID = parentID
		self.name = name
		self.remotePath = remotePath
		self.localPath = localPath
		self.processingPath = None
		self.modifiedTime = rfcToTimestamp(modifiedTime) if modifiedTime else None
		self.files = {
			"strm": [],
			"video": [],
			"media_assets": {},
		}

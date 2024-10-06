import os

from helpers import rfcToTimestamp


class Folder:

	def __init__(self, id, parentID, rootFolderID, driveID, name, remotePath, localPath, syncRootPath, rename, modifiedTime=None):
		self.id = id
		self.parentID = parentID
		self.rootFolderID = rootFolderID
		self.driveID = driveID
		self.name = name
		self.remotePath = remotePath
		self.localPath = localPath
		self.syncRootPath = syncRootPath
		self.original = rename == False
		self.modifiedTime = rfcToTimestamp(modifiedTime) if modifiedTime else None
		self.processingPath = None
		self.files = {
			"strm": [],
			"video": [],
			"media_asset": [],
		}

		if rename:
			self.setProcessingPath()

	def setProcessingPath(self):
		self.processingPath = os.path.join(self.syncRootPath, "[gDrive] Processing", self.remotePath)

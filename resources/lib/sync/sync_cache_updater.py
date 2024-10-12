class SyncCacheUpdater:

	def __init__(self, cache):
		self.cache = cache
		self.directories = []
		self.files = []

	def addDirectories(self):
		self.cache.addDirectories(self.directories)

	def addDirectory(self, folder):
		self.directories.append(
			(
				folder.driveID,
				folder.rootFolderID,
				folder.parentID,
				folder.id,
				folder.remotePath,
				folder.name,
			)
		)

	def addFile(self, folder, file):
		originalFolder = folder.original
		fileType = file.type
		self.files.append(
			(
				folder.driveID,
				folder.rootFolderID,
				folder.id,
				file.id,
				False if originalFolder or fileType == "strm" else file.localPath,
				file.localName,
				file.remoteName,
				file.original,
				originalFolder if fileType != "strm" else True,
				True if fileType == "video" and file.metadata.get("video_duration") else False,
				file.modifiedTime,
			)
		)

	def addFiles(self):
		self.cache.addFiles(self.files)

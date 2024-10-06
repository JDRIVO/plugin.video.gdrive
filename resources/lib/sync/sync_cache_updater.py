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
		self.files.append(
			(
				folder.driveID,
				folder.rootFolderID,
				folder.id,
				file.id,
				False if folder.original or file.type == "strm" else file.localPath,
				file.localName,
				file.remoteName,
				file.original,
				folder.original if file.type != "strm" else True,
			)
		)

	def addFiles(self):
		self.cache.addFiles(self.files)

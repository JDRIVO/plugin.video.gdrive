import os

from .folder import Folder
from .file_maker import makeFile
from .fs_constants import MEDIA_ASSETS
from .fs_helpers import removeProhibitedFSchars
from ..threadpool.threadpool import ThreadPool


class FileTree:

	def __init__(self, fileProcessor, cloudService, cache, cacheUpdater, driveID, syncRootPath, drivePath, renameFolder, renameFile, threadCount, encryptor, excludedTypes, syncedIDs):
		self.fileProcessor = fileProcessor
		self.cloudService = cloudService
		self.cache = cache
		self.cacheUpdater = cacheUpdater
		self.driveID = driveID
		self.syncRootPath = syncRootPath
		self.drivePath = drivePath
		self.renameFolder = renameFolder
		self.renameFile = renameFile
		self.threadCount = threadCount
		self.encryptor = encryptor
		self.excludedTypes = excludedTypes
		self.syncedIDs = syncedIDs
		self.rename = renameFile or renameFolder
		self.folderIDs = []
		self.fileTree = {}

	def __iter__(self):
		return iter(self.fileTree.values())

	def buildTree(self, rootFolder):
		self.cacheUpdater.addDirectory(rootFolder)
		self.rootFolderID = rootFolder.id
		self.folderIDs.append(self.rootFolderID)
		self.fileTree[self.rootFolderID] = rootFolder
		self._getContents()

	def _getContents(self):
		maxIDs = 299
		queries = []

		while self.folderIDs:
			ids = self.folderIDs[:maxIDs]
			queries.append(
				(
					"not trashed and (" + " or ".join(f"'{id}' in parents" for id in ids) + ")",
					ids,
				)
			)
			self.folderIDs = self.folderIDs[maxIDs:]

		def getFolders(query, parentFolderIDs):
			items = self.cloudService.listDirectory(customQuery=query)
			self._filterContents(items, parentFolderIDs)

		with ThreadPool(self.threadCount) as pool:
			pool.map(getFolders, queries)

		if self.folderIDs:
			self._getContents()

	def _filterContents(self, items, parentFolderIDs):
		paths = set()

		for item in items:
			id = item["id"]
			parentFolderID = item["parents"][0]
			mimeType = item["mimeType"]
			isFolder = mimeType == "application/vnd.google-apps.folder"

			if self.syncedIDs:
				self.syncedIDs.append(id)

				if isFolder and self.cache.getDirectory({"folder_id": id}):
					continue

			if isFolder:
				folderName = removeProhibitedFSchars(item["name"])
				path = path_ = os.path.join(self.fileTree[parentFolderID].remotePath, folderName)
				copy = 1

				if self.syncedIDs:
					path = self.cache.getUniqueDirectoryPath(self.driveID, path, paths=paths)

				while path.lower() in paths:
					path = f"{path_} ({copy})"
					copy += 1

				folder = Folder(id, parentFolderID, self.rootFolderID, self.driveID, folderName, path, os.path.join(self.drivePath, path), self.syncRootPath, self.renameFolder, item["modifiedTime"])
				self.fileTree[id] = folder
				self.cacheUpdater.addDirectory(folder)
				paths.add(path.lower())
				self.folderIDs.append(id)
			else:
				file = makeFile(item, self.excludedTypes, self.encryptor, self.renameFile)

				if not file:
					continue

				self.fileProcessor.addFile((file, self.fileTree[parentFolderID]))

				if self.rename:
					files = self.fileTree[parentFolderID].files

					if file.type in MEDIA_ASSETS:
						files["media_asset"].append(file)
					else:
						files[file.type].append(file)

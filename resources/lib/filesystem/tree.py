import os

from . import helpers
from .folder import Folder
from .constants import MEDIA_ASSETS
from ..threadpool import threadpool


class FileTree:

	def __init__(self, cloudService, cache, driveID, drivePath, progressDialog, threadCount, encrypter, excludedTypes, syncedIDs):
		self.cloudService = cloudService
		self.cache = cache
		self.driveID = driveID
		self.drivePath = drivePath
		self.progressDialog = progressDialog
		self.threadCount = threadCount
		self.encrypter = encrypter
		self.excludedTypes = excludedTypes
		self.syncedIDs = syncedIDs
		self.folderIDs = []
		self.fileTree = {}

	def __iter__(self):
		return iter(self.fileTree.values())

	def buildTree(self, rootFolder):
		rootFolderID = rootFolder.id
		self.folderIDs.append(rootFolderID)
		self.fileTree[rootFolderID] = rootFolder
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

		with threadpool.ThreadPool(self.threadCount) as pool:
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
				folderName = helpers.removeProhibitedFSchars(item["name"])
				path = path_ = os.path.join(self.fileTree[parentFolderID].remotePath, folderName)
				copy = 1

				if self.syncedIDs:
					path = self.cache.getUniqueDirectoryPath(self.driveID, path, paths=paths)

				while path.lower() in paths:
					path = f"{path_} ({copy})"
					copy += 1

				paths.add(path.lower())
				self.folderIDs.append(id)
				self.fileTree[id] = Folder(id, parentFolderID, folderName, path, os.path.join(self.drivePath, path), item["modifiedTime"])
			else:
				file = helpers.makeFile(item, self.excludedTypes, self.encrypter)

				if not file:
					continue

				if self.progressDialog:
					self.progressDialog.incrementFile()

				files = self.fileTree[parentFolderID].files

				if file.type in MEDIA_ASSETS:
					files["media_assets"].setdefault(file.ptnName, []).append(file)
				else:
					files[file.type].append(file)

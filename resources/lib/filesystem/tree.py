import os

from . import helpers
from .constants import *
from .folder import Folder
from ..threadpool import threadpool


class FileTree:

	def __init__(self, cloudService, cache, drivePath, progressDialog, threadCount, encrypter, excludedTypes, syncedIDs):
		self.cloudService = cloudService
		self.cache = cache
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

	def buildTree(self, driveID, rootFolderID, folderID, parentFolderID, folderName, path, modifiedTime):
		self.folderIDs.append(folderID)
		self.fileTree[folderID] = Folder(folderID, parentFolderID, folderName, path, os.path.join(self.drivePath, path), modifiedTime)
		self._getContents(driveID, rootFolderID)

	def _getContents(self, driveID, rootFolderID):
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
			self._filterContents(items, driveID, rootFolderID, parentFolderIDs)

		with threadpool.ThreadPool(self.threadCount) as pool:
			pool.map(getFolders, queries)

		if self.folderIDs:
			self._getContents(driveID, rootFolderID)

	def _filterContents(self, items, driveID, rootFolderID, parentFolderIDs):
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
					path = self.cache.getUniqueDirectoryPath(driveID, path, paths=paths)

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

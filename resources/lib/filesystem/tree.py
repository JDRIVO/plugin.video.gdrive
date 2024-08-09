import os

from . import helpers
from .constants import *
from .folder import Folder
from ..threadpool import threadpool


class FileTree:

	def __init__(self, cloudService, dialogProgress, threadCount, encrypter, excludedTypes):
		self.cloudService = cloudService
		self.dialogProgress = dialogProgress
		self.threadCount = threadCount
		self.encrypter = encrypter
		self.excludedTypes = excludedTypes
		self.fileTree = {}

	def __iter__(self):
		return iter(self.fileTree.values())

	def buildTree(self, driveID, rootFolderID, folderID, parentFolderID, path):
		folderIDs = [folderID]
		folderName = os.path.basename(path)
		self.fileTree[folderID] = Folder(folderID, parentFolderID, folderName, path)
		self.getContents(driveID, rootFolderID, folderIDs)

	def getContents(self, driveID, rootFolderID, folderIDs):
		maxIDs = 299
		queries = []

		while folderIDs:
			ids = folderIDs[:maxIDs]
			queries.append(
				(
					"not trashed and (" + " or ".join(f"'{id}' in parents" for id in ids) + ")",
					ids,
				)
			)
			folderIDs = folderIDs[maxIDs:]

		def getFolders(query, parentFolderIDs):
			items = self.cloudService.listDirectory(customQuery=query)
			self.filterContents(items, driveID, rootFolderID, parentFolderIDs, folderIDs)

		with threadpool.ThreadPool(self.threadCount) as pool:
			pool.map(getFolders, queries)

		if folderIDs:
			self.getContents(driveID, rootFolderID, folderIDs)

	def filterContents(self, items, driveID, rootFolderID, parentFolderIDs, folderIDs):
		paths = []

		for item in items:
			id = item["id"]
			parentFolderID = item["parents"][0]
			mimeType = item["mimeType"]

			if mimeType == "application/vnd.google-apps.folder":
				folderName = helpers.removeProhibitedFSchars(item["name"])
				path = path_ = os.path.join(self.fileTree[parentFolderID].path, folderName)
				pathLowerCase = path.lower()
				copy = 1

				while pathLowerCase in paths:
					path = f"{path_} ({copy})"
					pathLowerCase = path.lower()
					copy += 1

				paths.append(pathLowerCase)
				folderIDs.append(id)
				self.fileTree[id] = Folder(id, parentFolderID, folderName, path)
				continue

			file = helpers.makeFile(item, self.excludedTypes, self.encrypter)

			if not file:
				continue

			if self.dialogProgress:
				self.dialogProgress.incrementFile()

			files = self.fileTree[parentFolderID].files

			if file.type in MEDIA_ASSETS:
				mediaAssets = files["media_assets"]

				if file.ptnName not in mediaAssets:
					mediaAssets[file.ptnName] = []

				mediaAssets[file.ptnName].append(file)

			else:
				files[file.type].append(file)

import os
import threading

from . import helpers
from .constants import *
from .folder import Folder
from ..threadpool import threadpool


class FileTree:
	lock = threading.Lock()

	def __init__(self, cloudService, cache, dialogProgress, threadCount, encrypter, excludedTypes, syncedIDs, excludedIDs):
		self.cloudService = cloudService
		self.cache = cache
		self.dialogProgress = dialogProgress
		self.threadCount = threadCount
		self.encrypter = encrypter
		self.excludedTypes = excludedTypes
		self.syncedIDs = syncedIDs
		self.excludedIDs = excludedIDs
		self.fileTree = {}

	def __iter__(self):
		return iter(self.fileTree.values())

	def buildTree(self, driveID, rootFolderID, folderID, parentFolderID, path):
		folderIDs = [folderID]
		folderName = os.path.basename(path)
		path_ = path
		copy = 1

		with self.lock:

			while self.cache.getDirectory({"local_path": path}):
				path = f"{path_} ({copy})"
				copy += 1

		directory = {
			"drive_id": driveID,
			"folder_id": folderID,
			"local_path": path,
			"remote_name": folderName,
			"parent_folder_id": parentFolderID,
			"root_folder_id": rootFolderID,
		}
		self.cache.addDirectory(directory)
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

			if id in self.excludedIDs:
				continue

			if self.syncedIDs is not None:
				self.syncedIDs.append(id)

			parentFolderID = item["parents"][0]
			mimeType = item["mimeType"]

			if mimeType == "application/vnd.google-apps.folder":
				folderName = helpers.removeProhibitedFSchars(item["name"])
				path = path_ = os.path.join(self.fileTree[parentFolderID].path, folderName)
				copy = 1

				while path in paths:
					path = f"{path_} ({copy})"
					copy += 1

				paths.append(path)
				folderIDs.append(id)
				directory = {
					"drive_id": driveID,
					"folder_id": id,
					"local_path": path,
					"remote_name": folderName,
					"parent_folder_id": parentFolderID,
					"root_folder_id": rootFolderID,
				}
				self.cache.addDirectory(directory)
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

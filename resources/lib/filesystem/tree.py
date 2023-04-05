import os

from . import helpers
from .constants import *
from .folder import Folder
from ..threadpool import threadpool


class FileTree:

	def __init__(self, cloudService):
		self.cloudService = cloudService

	def buildTree(self, folderID, parentFolderID, path, excludedTypes, encrypter, syncedIDs, threadCount):
		fileTree = dict()
		fileTree[folderID] = Folder(folderID, parentFolderID, path, path)
		yield from self.getContents(fileTree, [folderID], excludedTypes, encrypter, syncedIDs, threadCount)

	def getContents(self, fileTree, folderIDs, excludedTypes, encrypter, syncedIDs, threadCount):
		maxIDs = 299
		queries = []

		while folderIDs:
			ids = folderIDs[:maxIDs]
			queries.append("not trashed and " + " or ".join(f"'{id}' in parents" for id in ids))
			folderIDs = folderIDs[maxIDs:]

		with threadpool.ThreadPool(threadCount) as pool:

			for query in queries:
				items = self.cloudService.listDirectory(customQuery=query)
				yield from self.filterContents(fileTree, items, folderIDs, excludedTypes, encrypter, syncedIDs)

		if folderIDs:
			yield from self.getContents(fileTree, folderIDs, excludedTypes, encrypter, syncedIDs, threadCount)

	def filterContents(self, fileTree, items, folderIDs, excludedTypes, encrypter, syncedIDs):
		parentFolderIDs = set()

		for item in items:
			id = item["id"]
			parentFolderID = item["parents"][0]
			mimeType = item["mimeType"]

			if syncedIDs is not None:
				syncedIDs.append(id)

			if mimeType == "application/vnd.google-apps.folder":
				folderName = item["name"]
				path = os.path.join(fileTree[parentFolderID].path, helpers.removeProhibitedFSchars(folderName))
				fileTree[id] = Folder(id, parentFolderID, folderName, path)
				folderIDs.append(id)
				parentFolderIDs.add(parentFolderID)
				continue

			file = helpers.makeFile(item, excludedTypes, encrypter)

			if not file:
				continue

			parentFolderIDs.add(parentFolderID)
			files = fileTree[parentFolderID].files

			if file.type in MEDIA_ASSETS:
				mediaAssets = files["media_assets"]

				if file.ptn_name not in mediaAssets:
					mediaAssets[file.ptn_name] = []

				mediaAssets[file.ptn_name].append(file)
			else:
				files[file.type].append(file)

		for id in parentFolderIDs:
			yield fileTree[id]

import os
from threading import Thread

from . import helpers


class FileTree:

	def __init__(self, cloudService):
		self.cloudService = cloudService

	@staticmethod
	def getNode(parentFolderID, remotePath):
		return {
			"parent_folder_id": parentFolderID,
			"path": remotePath,
			"files": {
				"strm": [],
				"video": [],
				"media_assets": {},
			},
			"directories": [],
		}

	def buildTree(self, folderID, path, excludedTypes, encrypter, syncedIDs):
		fileTree = dict()
		fileTree[folderID] = self.getNode(folderID, path)
		self.getContents(fileTree, [folderID], excludedTypes, encrypter, syncedIDs)
		return fileTree

	def getContents(self, fileTree, folderIDs, excludedTypes, encrypter, syncedIDs):
		maxIDs = 299
		queries = []

		while folderIDs:
			ids = folderIDs[:maxIDs]
			queries.append("not trashed and " + " or ".join(f"'{id}' in parents" for id in ids))
			folderIDs = folderIDs[maxIDs:]

		threads = []

		for query in queries:
			items = self.cloudService.listDirectory(customQuery=query)
			t = Thread(target=self.filterContents, args=(fileTree, items, folderIDs, excludedTypes, encrypter, syncedIDs))
			t.start()
			threads.append(t)

		for t in threads:
			t.join()

		if folderIDs:
			self.getContents(fileTree, folderIDs, excludedTypes, encrypter, syncedIDs)

	def filterContents(self, fileTree, items, folderIDs, excludedTypes, encrypter, syncedIDs):

		for item in items:
			id = item["id"]
			parentFolderID = item["parents"][0]
			mimeType = item["mimeType"]

			if syncedIDs is not None:
				syncedIDs.append(id)

			if mimeType == "application/vnd.google-apps.folder":
				path = os.path.join(fileTree[parentFolderID]["path"], helpers.removeProhibitedFSchars(item["name"]))
				fileTree[parentFolderID]["directories"].append(id)
				fileTree[id] = self.getNode(parentFolderID, path)
				folderIDs.append(id)
				continue

			file = helpers.makeFile(item, excludedTypes, encrypter)

			if not file:
				continue

			files = fileTree[parentFolderID]["files"]
			mediaAssets = files["media_assets"]

			if file.type in ("poster", "fanart", "subtitles", "nfo"):

				if file.ptn_name not in mediaAssets:
					mediaAssets[file.ptn_name] = {
						"nfo": [],
						"subtitles": [],
						"fanart": [],
						"poster": [],
					}

				mediaAssets[file.ptn_name][file.type].append(file)
			else:
				files[file.type].append(file)

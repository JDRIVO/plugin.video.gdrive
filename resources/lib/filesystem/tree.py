import os

from . import helpers
from . import processor


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

	def buildTree(self, tree, folderID, parentFolderID, path, excludedTypes, encrypter, syncedIDs):
		remoteFiles = self.cloudService.listDirectory(folderID)
		tree[folderID] = self.getNode(parentFolderID, path)
		files = tree[folderID]["files"]
		mediaAssets = files["media_assets"]

		for file in remoteFiles:
			fileID = file["id"]

			if syncedIDs is not None:
				syncedIDs.append(fileID)

			mimeType = file["mimeType"]

			if mimeType == "application/vnd.google-apps.folder":
				childPath = os.path.join(path, helpers.removeProhibitedFSchars(file["name"]))
				tree[folderID]["directories"].append(fileID)
				self.buildTree(tree, fileID, file["parents"][0], childPath, excludedTypes, encrypter, syncedIDs)
				continue

			file = helpers.makeFile(file, excludedTypes, encrypter)

			if not file:
				continue

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

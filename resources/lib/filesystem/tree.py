import os

from . import video
from . import helpers
from .file import File
from . import processor


class FileTree:

	def __init__(self, cloudService, encrypter):
		self.cloudService = cloudService
		self.encrypter = encrypter

	@staticmethod
	def createFileTree(parentFolderID, remotePath):
		return {
			"parent_folder_id": parentFolderID,
			"path": remotePath,
			"files": {
				"strm": [],
				"video": [],
				"subtitles": [],
				"nfo": [],
				"fanart": [],
				"posters": [],
			},
			"dirs": [],
		}

	def buildTree(self, folderID, parentFolderID, path, tree, hasEncryptedFiles):
		remoteFiles = self.cloudService.listDirectory(folderID)

		for file in remoteFiles:
			fileID = file["id"]
			filename = file["name"]
			mimeType = file["mimeType"]
			fileExtension = file.get("fileExtension")

			if hasEncryptedFiles and mimeType == "application/octet-stream" and not fileExtension:
				filename = self.encrypter.decryptFilename(filename)

				if not filename:
					continue

				fileExtension = filename.rsplit(".", 1)[-1]
				encrypted = True

			else:
				encrypted = False

			filename = helpers.removeProhibitedFSchars(filename)
			fileType = helpers.identifyFileType(filename, fileExtension, mimeType)

			if not fileType:
				continue

			folderDic = tree.get(folderID)

			if not folderDic:
				tree[folderID] = self.createFileTree(parentFolderID, path)

			if fileType == "folder":
				parentFolderID = file["parents"][0]
				newPath = os.path.join(path, filename)
				tree[folderID]["dirs"].append(fileID)
				tree[fileID] = self.createFileTree(parentFolderID, newPath)
				self.buildTree(fileID, parentFolderID, newPath, tree, hasEncryptedFiles)
			else:
				metadata = file.get("videoMediaMetadata")

				if fileType == "video":
					videoInfo = helpers.getVideoInfo(filename, metadata)
					mediaType = helpers.identifyMediaType(videoInfo)

					if mediaType == "episode":
						_file = video.Episode()
					elif mediaType == "movie":
						_file = video.Movie()
					else:
						_file = video.Video()

					_file.setContents(videoInfo)

				else:
					_file = File()

				_file.name = filename
				_file.id = file["id"]
				_file.metadata = metadata
				_file.encrypted = encrypted
				tree[folderID]["files"][fileType].append(_file)

		return tree

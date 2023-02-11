import os
import json

import xbmc

from . import cache
from . import helpers
from .. import filesystem


class Syncer:

	def __init__(self, accountManager, cloudService, encrypter, fileOperations, fileProcessor, fileTree, settings):
		self.encrypter = encrypter
		self.cloudService = cloudService
		self.accountManager = accountManager
		self.fileProcessor = fileProcessor
		self.fileTree = fileTree
		self.fileOperations = fileOperations
		self.settings = settings

	def syncChanges(self, driveID, syncSettings):
		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.cloudService.refreshToken()
		cloudData = syncSettings["drives"][driveID]

		changes, pageToken = self.cloudService.getChanges(cloudData["page_token"])
		changes.reverse()
		syncRoot = syncSettings["local_path"]
		cachedDirectories = cloudData["directories"]

		if not changes:
			return

		cachedDirectories = cloudData["directories"]
		cachedFiles = cloudData["files"]
		folders = cloudData["folders"]
		newFiles = {}
		self.deleted = False

		for change in changes:
			fileProperties = change["file"]
			parentFolderID = fileProperties.get("parents")

			if not parentFolderID:
				# file not inside a folder
				continue

			parentFolderID = parentFolderID[0]
			fileProperties["name"] = filesystem.helpers.removeProhibitedFSchars(fileProperties["name"])

			if fileProperties["trashed"]:
				self.syncDeletions(cachedDirectories, cachedFiles, syncRoot, fileProperties, parentFolderID)
			else:

				if fileProperties["mimeType"] == "application/vnd.google-apps.folder":
					self.syncFolderChanges(fileProperties, cachedDirectories, cachedFiles, folders, syncRoot, parentFolderID, driveID)
				else:
					self.syncFileChanges(fileProperties, parentFolderID, driveID, newFiles, cachedDirectories, cachedFiles, folders, syncRoot)

		if newFiles:
			self.syncFileAdditions(newFiles, syncRoot, folders, cachedDirectories, cachedFiles, driveID)
			xbmc.executebuiltin(f"UpdateLibrary(video,{syncRoot})")

		if self.deleted:

			if os.name == "nt":
				syncRoot = syncRoot.replace("\\", "\\\\")

			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.Clean", "params": {"showdialogs": false, "content": "video", "directory": "%s"}}' % syncRoot)

		cloudData["page_token"] = pageToken
		self.settings.saveSyncSettings(syncSettings)

	def syncDeletions(self, cachedDirectories, cachedFiles, syncRoot, fileProperties, parentFolderID):
		fileID = fileProperties["id"]

		if fileID not in cachedFiles and fileID not in cachedDirectories:
			return

		try:
			fileIDs = cachedDirectories[parentFolderID]["file_ids"]
		except KeyError:
			fileIDs = []

		if fileID in cachedFiles:
			cachedFile = cachedFiles[fileID]

			if cachedFile["original_folder"]:
				self.fileOperations.deleteFile(syncRoot, dirPath=cachedDirectories[parentFolderID]["local_path"], filename=cachedFile["local_name"])
			else:
				self.fileOperations.deleteFile(syncRoot, filePath=cachedFile["local_path"])

			del cachedFiles[fileID]

			if fileID in fileIDs:
				fileIDs.remove(fileID)

		if not fileIDs:

			try:
				del cachedDirectories[parentFolderID]
			except KeyError:
				pass

		if fileProperties["mimeType"] == "application/vnd.google-apps.folder":
			if fileID in cachedDirectories and not cachedDirectories[fileID]["file_ids"]:
				del cachedDirectories[fileID]

		self.deleted = True

	def syncFolderChanges(self, folder, cachedDirectories, cachedFiles, folders, syncRoot, parentFolderID, driveID):
		folderID = folder["id"]
		folderName = folder["name"]

		if folderID not in cachedDirectories:
			# New folder added
			dirPath, rootFolderID, rootPath = self.cloudService.getDirectory(cachedDirectories, folders, parentFolderID)

			if not rootFolderID:
				return

			dirPath = os.path.join(dirPath, folderName)
			directory = cache.directory()
			directory["local_path"] = dirPath
			directory["parent_folder_id"] = parentFolderID if parentFolderID != driveID else folderID
			directory["root_folder_id"] = rootFolderID
			directory["folder_ids"] = []
			directory["file_ids"] = []
			cachedDirectories[folderID] = directory
			helpers.addFolderIDtoCachedList(cachedDirectories, parentFolderID, folderID)
			self.syncFolderAdditions(syncRoot, dirPath, folders[rootFolderID], cachedDirectories, cachedFiles, parentFolderID, folderID, rootFolderID, driveID)
			return

		# Existing folder
		cachedDirectory = cachedDirectories[folderID]
		cachedDirPath = cachedDirectory["local_path"]
		cachedParentFolderID = cachedDirectory["parent_folder_id"]
		cachedRootFolderID = cachedDirectory["root_folder_id"]
		folderIDs = cachedDirectory["folder_ids"]
		fileIDs = cachedDirectory["file_ids"]

		cachedDirPathHead, dirName = cachedDirPath.rsplit(os.sep, 1)

		# if not os.path.exists(cachedDirPath) and fileIDs:
			# redownload

		if parentFolderID != cachedParentFolderID and folderID != cachedRootFolderID:
			# folder has been moved into another directory
			dirPath, rootFolderID, rootPath = self.cloudService.getDirectory(cachedDirectories, folders, parentFolderID)

			if dirPath:
				newDirPath = os.path.join(dirPath, folderName)
				self.fileOperations.renameFolder(syncRoot, cachedDirPath, newDirPath)
				oldPath = cachedDirectory["local_path"]
				cachedDirectory["local_path"] = newDirPath
				cachedDirectory["parent_folder_id"] = parentFolderID
				helpers.removeFolderIDfromCachedList(cachedDirectories, cachedParentFolderID, folderID)
				helpers.addFolderIDtoCachedList(cachedDirectories, parentFolderID, folderID)

				for folderID in folderIDs:
					helpers.updateCachedPaths(oldPath, newDirPath, cachedDirectories, folderID)

			else:
				# Folder moved to another root folder != existing root folder - delete current folder
				self.fileOperations.deleteFiles(syncRoot, folderID, cachedDirectories, cachedFiles)
				cachedDirectories[cachedParentFolderID]["folder_ids"].remove(folderID)
				self.deleted = True

		elif dirName != folderName:
			# folder name has been changed
			newDirPath = os.path.join(cachedDirPathHead, folderName)
			self.fileOperations.renameFolder(syncRoot, cachedDirPath, newDirPath)
			cachedDirectory["local_path"] = newDirPath

			if folderID == cachedRootFolderID:
				folders[folderID]["local_path"] = newDirPath

	def syncFileChanges(self, file, parentFolderID, driveID, newFiles, cachedDirectories, cachedFiles, folders, syncRoot):
		fileID = file["id"]

		if parentFolderID not in cachedDirectories:
			dirPath, rootFolderID, rootPath = self.cloudService.getDirectory(cachedDirectories, folders, parentFolderID)

			if not rootFolderID:

				if fileID in cachedFiles:
					# file has moved outside of root folder hierarchy/tree
					cachedFile = cachedFiles[fileID]
					cachedParentFolderID = cachedFile["parent_folder_id"]

					if cachedFile["original_folder"]:
						cachedFilePath = os.path.join(cachedDirectories[cachedParentFolderID]["local_path"], cachedFile["local_name"])
					else:
						cachedFilePath = cachedFile["local_path"]

					self.fileOperations.deleteFile(syncRoot, filePath=cachedFilePath)
					self.deleted = True
					del cachedFiles[fileID]
					helpers.removeFileIDfromCachedList(cachedDirectories, cachedParentFolderID, fileID)

				return

			# file added to synced folder but the directory isn't present locally
			dirParentFolderID = self.cloudService.getParentDirectoryID(parentFolderID)
			directory = cache.directory()
			directory["local_path"] = dirPath
			directory["parent_folder_id"] = dirParentFolderID if dirParentFolderID != driveID else parentFolderID
			directory["root_folder_id"] = rootFolderID
			directory["folder_ids"] = []
			directory["file_ids"] = []
			cachedDirectories[parentFolderID] = directory
			helpers.addFolderIDtoCachedList(cachedDirectories, dirParentFolderID, parentFolderID)

		else:
			cachedDirectory = cachedDirectories[parentFolderID]
			dirPath = cachedDirectory["local_path"]
			cachedParentFolderID = cachedDirectory["parent_folder_id"]
			rootFolderID = cachedDirectory["root_folder_id"]
			folderIDs = cachedDirectory["folder_ids"]
			fileIDs = cachedDirectory["file_ids"]

		filename = file["name"]
		fileExtension = file.get("fileExtension")
		mimeType = file["mimeType"]
		folderSettings = folders[rootFolderID]
		encrypted = folderSettings["contains_encrypted"]

		if encrypted and mimeType == "application/octet-stream" and not fileExtension:
			filename = self.encrypter.decryptFilename(filename)

			if not filename:
				return

			fileExtension = filename.rsplit(".", 1)[-1]
		else:
			encrypted = False

		fileType = filesystem.helpers.identifyFileType(filename, fileExtension, mimeType)
		refreshMetadata = False

		if not fileType:
			return

		metadata = file.get("videoMediaMetadata")

		if fileType == "video":
			videoInfo = filesystem.helpers.getVideoInfo(filename, metadata)
			mediaType = filesystem.helpers.identifyMediaType(videoInfo)

			if mediaType == "episode":
				file = filesystem.video.Episode()
			elif mediaType == "movie":
				file = filesystem.video.Movie()
			else:
				file = filesystem.video.Video()

			file.setContents(videoInfo)

		else:
			file = filesystem.file.File()

		if fileID in cachedFiles:
			cachedFile = cachedFiles[fileID]
			cachedParentFolderID = cachedFile["parent_folder_id"]

			cachedDirectory = cachedDirectories[cachedParentFolderID]
			cachedDirPath = cachedDirectory["local_path"]
			rootFolderID = cachedDirectory["root_folder_id"]
			folderIDs = cachedDirectory["folder_ids"]
			fileIDs = cachedDirectory["file_ids"]

			if cachedFile["original_folder"]:
				cachedFilePath = os.path.join(cachedDirPath, cachedFile["local_name"])
			else:
				cachedFilePath = cachedFile["local_path"]

			if os.path.splitext(cachedFile["remote_name"])[0] == os.path.splitext(filename)[0] and cachedDirPath == dirPath:
				# this needs to be done as GDRIVE creates multiple changes for a file, one before its metadata is processed and another change after the metadata is processed
				self.fileOperations.deleteFile(syncRoot, filePath=cachedFilePath)
				self.deleted = True
				del cachedFiles[fileID]
				fileIDs.remove(fileID)
				refreshMetadata = True

			elif cachedFile["original_name"]:

				if not os.path.exists(cachedFilePath):
					# file doesn't exist locally - redownload it
					del cachedFiles[fileID]
					fileIDs.remove(fileID)
				else:
					# rename/move file
					filenameWithoutExt = os.path.splitext(filename)[0]
					fileExtension = os.path.splitext(cachedFile["local_name"])[1]
					newFilename = filenameWithoutExt + fileExtension

					if cachedFile["original_folder"]:
						self.fileOperations.renameFile(syncRoot, cachedFilePath, dirPath, newFilename)
					else:
						newFilePath = self.fileOperations.renameFile(syncRoot, cachedFilePath, os.path.dirname(cachedFile), newFilename)
						cachedFile["local_path"] = newFilePath

					cachedFile["local_name"] = newFilename
					cachedFile["remote_name"] = filename

					if parentFolderID != cachedParentFolderID:
						fileIDs.remove(fileID)
						cachedDirectories[parentFolderID]["file_ids"].append(fileID)

					return

			else:
				# redownload file
				self.fileOperations.deleteFile(syncRoot, filePath=cachedFilePath)
				self.deleted = True
				del cachedFiles[fileID]
				fileIDs.remove(fileID)

		if not newFiles.get(rootFolderID):
			newFiles[rootFolderID] = {}
			newFiles[rootFolderID][parentFolderID] = self.fileTree.createFileTree(parentFolderID, dirPath)
		else:

			if not newFiles[rootFolderID].get(parentFolderID):
				newFiles[rootFolderID][parentFolderID] = self.fileTree.createFileTree(parentFolderID, dirPath)

		file.name = filename
		file.id = fileID
		file.metadata = metadata
		file.encrypted = encrypted
		file.refresh_metadata = refreshMetadata
		newFiles[rootFolderID][parentFolderID]["files"][fileType].append(file)

	def syncFolderAdditions(self, syncRoot, dirPath, folderSettings, cachedDirectories, cachedFiles, parentFolderID, folderID, rootFolderID, driveID):
		folderRoot = folderSettings["local_path"]
		encrypted = folderSettings["contains_encrypted"]
		fileTree = self.fileTree.buildTree(folderID, parentFolderID, dirPath, {}, encrypted)

		for folderID, folderInfo in fileTree.items():
			remotePath = folderInfo["path"]
			parentFolderID = folderInfo["parent_folder_id"]
			dirPath = os.path.join(folderRoot, remotePath)

			directory = cache.directory()
			directory["local_path"] = dirPath
			directory["parent_folder_id"] = parentFolderID
			directory["root_folder_id"] = rootFolderID
			directory["folder_ids"] = folderInfo["dirs"]
			directory["file_ids"] = []
			cachedDirectories[folderID] = directory

			self.fileProcessor.processFiles(cachedDirectories, cachedFiles, folderInfo["files"], folderSettings, dirPath, syncRoot, driveID, folderID)

	def syncFileAdditions(self, files, syncRoot, folders, cachedDirectories, cachedFiles, driveID):

		for folderID, subFolderDic in files.items():

			for subFolderID, tree in subFolderDic.items():
				folderSettings = folders[folderID]
				remotePath = tree["path"]
				parentFolderID = tree["parent_folder_id"]
				self.fileProcessor.processFiles(cachedDirectories, cachedFiles, tree["files"], folderSettings, remotePath, syncRoot, driveID, parentFolderID)

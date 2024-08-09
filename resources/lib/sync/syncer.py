import os

import xbmc

from .. import filesystem
from ..threadpool import threadpool
from ..filesystem.constants import *
from ..filesystem.tree import FileTree
from ..filesystem.folder import Folder


class Syncer:

	def __init__(self, accountManager, cloudService, encrypter, fileOperations, settings, cache):
		self.accountManager = accountManager
		self.cloudService = cloudService
		self.encrypter = encrypter
		self.fileOperations = fileOperations
		self.settings = settings
		self.cache = cache
		self.remoteFileProcessor = filesystem.processor.RemoteFileProcessor(self.cloudService, self.fileOperations, self.settings, self.cache)
		self.localFileProcessor = filesystem.processor.LocalFileProcessor(self.cloudService, self.fileOperations, self.settings, self.cache)

	def sortChanges(self, changes):
		trashed, existingFolders, newFolders, files = [], [], [], []

		for change in changes:
			item = change["file"]

			if item["trashed"]:
				trashed.append(item)
				continue

			item["name"] = filesystem.helpers.removeProhibitedFSchars(item["name"])

			if item["mimeType"] == "application/vnd.google-apps.folder":
				cachedDirectory = self.cache.getDirectory({"folder_id": item["id"]})

				if cachedDirectory:
					existingFolders.append(item)
				else:
					newFolders.append(item)

			else:
				files.append(item)

		return trashed + existingFolders + newFolders + files

	def syncChanges(self, driveID):
		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.cloudService.refreshToken()
		syncRootPath = self.cache.getSyncRootPath()
		driveSettings = self.cache.getDrive(driveID)
		drivePath = driveSettings["local_path"]
		changes, pageToken = self.cloudService.getChanges(driveSettings["page_token"])

		if not changes:
			return

		changes = self.sortChanges(changes)
		self.deleted = False
		newFiles = {}

		for item in changes:
			id = item["id"]

			try:
				# shared items that google automatically adds to an account don't have parentFolderIDs
				parentFolderID = item["parents"][0]
			except:
				continue

			if item["trashed"]:
				self.syncDeletions(item, syncRootPath, drivePath)
				continue

			if item["mimeType"] == "application/vnd.google-apps.folder":
				self.syncFolderChanges(item, parentFolderID, driveID, syncRootPath, drivePath)
			else:
				self.syncFileChanges(item, parentFolderID, driveID, syncRootPath, drivePath, newFiles)

		if newFiles:
			self.syncFileAdditions(newFiles, drivePath, syncRootPath, driveID)

			if self.settings.getSetting("update_library"):
				xbmc.executebuiltin(f"UpdateLibrary(video,{syncRootPath})")

		if self.deleted and self.settings.getSetting("update_library"):

			if os.name == "nt":
				syncRootPath = syncRootPath.replace("\\", "\\\\")

			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.Clean", "params": {"showdialogs": false, "content": "video", "directory": "%s"}}' % syncRootPath)

		self.cache.updateDrive({"page_token": pageToken}, driveID)

	def syncDeletions(self, item, syncRootPath, drivePath):
		id = item["id"]
		cachedFiles = True

		if item["mimeType"] == "application/vnd.google-apps.folder":
			cachedFiles = self.cache.getFile({"parent_folder_id": id})
			folderID = id
		else:
			cachedFile = self.cache.getFile({"file_id": id})

			if not cachedFile:
				return

			self.cache.deleteFile(id)
			folderID = cachedFile["parent_folder_id"]
			cachedDirectory = self.cache.getDirectory({"folder_id": folderID})
			cachedFiles = self.cache.getFile({"parent_folder_id": folderID})

			if cachedFile["original_folder"]:
				dirPath = os.path.join(syncRootPath, drivePath, cachedDirectory["local_path"])
				self.fileOperations.deleteFile(syncRootPath, dirPath, cachedFile["local_name"])
			else:
				filePath = os.path.join(syncRootPath, cachedFile["local_path"])
				self.fileOperations.deleteFile(syncRootPath, filePath=filePath)

		if not cachedFiles:
			cachedDirectory = self.cache.getDirectory({"folder_id": folderID})

			if not cachedDirectory:
				return

			self.cache.deleteDirectory(folderID)

		self.deleted = True

	def syncFolderChanges(self, folder, parentFolderID, driveID, syncRootPath, drivePath):
		folderID = folder["id"]
		folderName = folder["name"]
		cachedDirectory = self.cache.getDirectory({"folder_id": folderID})

		if not cachedDirectory:
			# new folder added
			dirPath, rootFolderID = self.cloudService.getDirectory(self.cache, folderID)

			if not rootFolderID:
				return

			dirPath = self.cache.getUniqueDirectory(driveID, dirPath)
			directory = {
				"drive_id": driveID,
				"folder_id": folderID,
				"local_path": dirPath,
				"remote_name": folderName,
				"parent_folder_id": parentFolderID,
				"root_folder_id": rootFolderID,
			}
			self.cache.addDirectory(directory)
			return

		# existing folder
		cachedDirectoryPath = cachedDirectory["local_path"]
		cachedParentFolderID = cachedDirectory["parent_folder_id"]
		cachedRootFolderID = cachedDirectory["root_folder_id"]

		if parentFolderID != cachedParentFolderID and folderID != cachedRootFolderID:
			# folder has been moved into another directory
			dirPath, rootFolderID = self.cloudService.getDirectory(self.cache, folderID)

			if not dirPath:
				# folder moved to another root folder != existing root folder > delete current folder
				drivePath = os.path.join(syncRootPath, drivePath)
				self.cache.removeDirectories(syncRootPath, drivePath, folderID, True, False)
				self.deleted = True
			else:
				self.cache.updateDirectory({"parent_folder_id": parentFolderID}, folderID)
				cachedParentDirectory = self.cache.getDirectory({"folder_id": parentFolderID})

				if cachedParentDirectory:
					dirPath = self.cache.getUniqueDirectory(driveID, dirPath)
				else:
					parentDirPath = os.path.split(dirPath)[0]
					parentFolderName = os.path.basename(parentDirPath)
					parentDirPath = self.cache.getUniqueDirectory(driveID, parentDirPath)
					dirPath = os.path.join(parentDirPath, folderName)
					dirPath = self.cache.getUniqueDirectory(driveID, dirPath)
					parentsParentFolderID = self.cloudService.getParentDirectoryID(parentFolderID)
					directory = {
						"drive_id": driveID,
						"folder_id": parentFolderID,
						"local_path": parentDirPath,
						"remote_name": parentFolderName,
						"parent_folder_id": parentsParentFolderID if parentsParentFolderID != driveID else parentFolderID,
						"root_folder_id": rootFolderID,
					}
					self.cache.addDirectory(directory)

				oldPath = os.path.join(syncRootPath, drivePath, cachedDirectoryPath)
				newPath = os.path.join(syncRootPath, drivePath, dirPath)
				self.fileOperations.renameFolder(syncRootPath, oldPath, newPath)
				self.cache.updateChildPaths(cachedDirectoryPath, dirPath, folderID)

			return

		cachedRemoteName = cachedDirectory["remote_name"]

		if cachedRemoteName != folderName:
			# folder renamed
			cachedDirectoryPathHead, _ = os.path.split(cachedDirectoryPath)
			newDirectoryPath = newDirectoryPath_ = os.path.join(cachedDirectoryPathHead, folderName)
			newDirectoryPath = self.cache.getUniqueDirectory(driveID, newDirectoryPath)
			oldPath = os.path.join(syncRootPath, drivePath, cachedDirectoryPath)
			newPath = os.path.join(syncRootPath, drivePath, newDirectoryPath)
			self.fileOperations.renameFolder(syncRootPath, oldPath, newPath)
			self.cache.updateChildPaths(cachedDirectoryPath, newDirectoryPath, folderID)
			self.cache.updateDirectory({"remote_name": folderName}, folderID)

			if folderID == cachedRootFolderID:
				self.cache.updateFolder({"local_path": newDirectoryPath, "remote_name": folderName}, folderID)

	def syncFileChanges(self, file, parentFolderID, driveID, syncRootPath, drivePath, newFiles):
		fileID = file["id"]
		cachedDirectory = self.cache.getDirectory({"folder_id": parentFolderID})
		cachedFile = self.cache.getFile({"file_id": fileID})

		if cachedDirectory:
			dirPath = cachedDirectory["local_path"]
			cachedParentFolderID = cachedDirectory["parent_folder_id"]
			rootFolderID = cachedDirectory["root_folder_id"]
		else:
			dirPath, rootFolderID = self.cloudService.getDirectory(self.cache, parentFolderID)

			if not rootFolderID and cachedFile:
				# file has moved outside of root folder hierarchy/tree
				cachedParentFolderID = cachedFile["parent_folder_id"]
				cachedDirectory = self.cache.getDirectory({"folder_id": cachedParentFolderID})

				if cachedFile["original_folder"]:
					cachedFilePath = os.path.join(syncRootPath, drivePath, cachedDirectory["local_path"], cachedFile["local_name"])
				else:
					cachedFilePath = os.path.join(syncRootPath, cachedFile["local_path"])

				self.fileOperations.deleteFile(syncRootPath, filePath=cachedFilePath)
				self.cache.deleteFile(fileID)
				self.deleted = True
				return

			folderName = os.path.basename(dirPath)
			dirPath = self.cache.getUniqueDirectory(driveID, dirPath)
			parentsParentFolderID = self.cloudService.getParentDirectoryID(parentFolderID)
			directory = {
				"drive_id": driveID,
				"folder_id": parentFolderID,
				"local_path": dirPath,
				"remote_name": folderName,
				"parent_folder_id": parentsParentFolderID if parentsParentFolderID != driveID else parentFolderID,
				"root_folder_id": rootFolderID,
			}
			self.cache.addDirectory(directory)

		folderSettings = self.cache.getFolder({"folder_id": rootFolderID})
		excludedTypes = filesystem.helpers.getExcludedTypes(folderSettings)

		if folderSettings["contains_encrypted"]:
			encrypter = self.encrypter
		else:
			encrypter = None

		file = filesystem.helpers.makeFile(file, excludedTypes, encrypter)

		if not file:
			return

		filename = file.name

		if cachedFile:
			cachedParentFolderID = cachedFile["parent_folder_id"]
			cachedDirectory = self.cache.getDirectory({"folder_id": cachedParentFolderID})
			cachedDirPath = cachedDirectory["local_path"]
			rootFolderID = cachedDirectory["root_folder_id"]

			if cachedFile["original_folder"]:
				cachedFilePath = os.path.join(syncRootPath, drivePath, cachedDirPath, cachedFile["local_name"])
			else:
				cachedFilePath = os.path.join(syncRootPath, cachedFile["local_path"])

			if not cachedFile["original_name"] or not os.path.exists(cachedFilePath) or (cachedFile["remote_name"] == filename and cachedDirPath == dirPath):
				# new filename needs to be processed or file not existent or file contents modified > redownload file
				self.fileOperations.deleteFile(syncRootPath, filePath=cachedFilePath)
				self.cache.deleteFile(fileID)
				self.deleted = True
			else:
				# file either moved or renamed
				newFilename = file.basename + os.path.splitext(cachedFile["local_name"])[1]

				if cachedFile["original_folder"]:
					dirPath = os.path.join(syncRootPath, drivePath, dirPath)
					self.fileOperations.renameFile(syncRootPath, cachedFilePath, dirPath, newFilename)
				else:
					newFilePath = self.fileOperations.renameFile(syncRootPath, cachedFilePath, os.path.dirname(cachedFilePath), newFilename)
					cachedFile["local_path"] = newFilePath

				cachedFile["local_name"] = newFilename
				cachedFile["remote_name"] = filename
				cachedFile["parent_folder_id"] = parentFolderID
				self.cache.updateFile(cachedFile, fileID)
				return

		if not newFiles.get(rootFolderID):
			newFiles[rootFolderID] = {}
			newFiles[rootFolderID][parentFolderID] = Folder(parentFolderID, parentFolderID, dirPath, dirPath)
		else:

			if not newFiles[rootFolderID].get(parentFolderID):
				newFiles[rootFolderID][parentFolderID] = Folder(parentFolderID, parentFolderID, dirPath, dirPath)

		if file.type in MEDIA_ASSETS:
			mediaAssets = newFiles[rootFolderID][parentFolderID].files["media_assets"]

			if file.ptnName not in mediaAssets:
				mediaAssets[file.ptnName] = []

			mediaAssets[file.ptnName].append(file)
		else:
			newFiles[rootFolderID][parentFolderID].files[file.type].append(file)

	def syncFolderAdditions(self, syncRootPath, drivePath, dirPath, folderSettings, folderID, driveID, progressDialog):
		rootFolderID = parentFolderID = folderID

		if folderSettings["contains_encrypted"]:
			encrypter = self.encrypter
		else:
			encrypter = False

		excludedTypes = filesystem.helpers.getExcludedTypes(folderSettings)
		threadCount = self.settings.getSettingInt("thread_count", 1)
		folderRestructure = folderSettings["folder_restructure"]
		fileRenaming = folderSettings["file_renaming"]
		fileTree = FileTree(self.cloudService, progressDialog, threadCount, encrypter, excludedTypes)
		fileTree.buildTree(driveID, rootFolderID, folderID, parentFolderID, dirPath)

		with threadpool.ThreadPool(threadCount) as pool:

			for folder in fileTree:
				directory = {
					"drive_id": driveID,
					"folder_id": folder.id,
					"local_path": folder.path,
					"remote_name": folder.name,
					"parent_folder_id": folder.parentID,
					"root_folder_id": rootFolderID,
				}
				self.cache.addDirectory(directory)
				pool.submit(self.remoteFileProcessor.processFiles, folder, folderSettings, drivePath, syncRootPath, driveID, rootFolderID, threadCount, progressDialog)

		if progressDialog:
			progressDialog.processFolder()

		if not folderRestructure and not fileRenaming:
			return

		with threadpool.ThreadPool(threadCount) as pool:

			for folder in fileTree:
				pool.submit(self.localFileProcessor.processFiles, folder, folderSettings, drivePath, syncRootPath, threadCount, progressDialog)

	def syncFileAdditions(self, files, drivePath, syncRootPath, driveID):
		threadCount = self.settings.getSettingInt("thread_count", 1)
		folders = []

		with threadpool.ThreadPool(threadCount) as pool:

			for rootFolderID, directories in files.items():
				folderSettings = self.cache.getFolder({"folder_id": rootFolderID})
				folderRestructure = folderSettings["folder_restructure"]
				fileRenaming = folderSettings["file_renaming"]

				for folderID, folder in directories.items():
					pool.submit(self.remoteFileProcessor.processFiles, folder, folderSettings, drivePath, syncRootPath, driveID, rootFolderID, threadCount)

					if folderRestructure or fileRenaming:
						folders.append((folder, folderSettings))

		with threadpool.ThreadPool(threadCount) as pool:

			for folder, folderSettings in folders:
				pool.submit(self.localFileProcessor.processFiles, folder, folderSettings, drivePath, syncRootPath, threadCount)

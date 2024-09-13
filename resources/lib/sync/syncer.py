import os

import xbmc

from ..filesystem.folder import Folder
from ..filesystem.fs_tree import FileTree
from ..filesystem.fs_constants import MEDIA_ASSETS
from ..filesystem.file_processor import LocalFileProcessor, RemoteFileProcessor
from ..filesystem.fs_helpers import getExcludedTypes, makeFile, removeProhibitedFSchars
from ..threadpool.threadpool import ThreadPool


class Syncer:

	def __init__(self, accountManager, cloudService, encryptor, fileOperations, settings, cache):
		self.accountManager = accountManager
		self.cloudService = cloudService
		self.encryptor = encryptor
		self.fileOperations = fileOperations
		self.settings = settings
		self.cache = cache
		self.remoteFileProcessor = RemoteFileProcessor(self.cloudService, self.fileOperations, self.settings, self.cache)
		self.localFileProcessor = LocalFileProcessor(self.cloudService, self.fileOperations, self.settings, self.cache)

	def syncChanges(self, driveID):
		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.cloudService.refreshToken()
		driveSettings = self.cache.getDrive(driveID)
		syncRootPath = self.cache.getSyncRootPath()
		drivePath = os.path.join(syncRootPath, driveSettings["local_path"])
		changes, pageToken = self.cloudService.getChanges(driveSettings["page_token"])

		if not changes or not pageToken:
			return

		changes = self._sortChanges(changes)
		self.deleted = False
		syncedIDs = []
		newFiles = {}

		for item in changes:
			id = item["id"]

			if id in syncedIDs:
				continue

			syncedIDs.append(id)

			try:
				# shared items that google automatically adds to an account don't have parentFolderIDs
				parentFolderID = item["parents"][0]
			except KeyError:
				continue

			if item["trashed"]:
				self._syncDeletions(item, syncRootPath, drivePath)
				continue

			if item["mimeType"] == "application/vnd.google-apps.folder":
				self._syncFolderChanges(item, parentFolderID, driveID, syncRootPath, drivePath, syncedIDs)
			else:
				self._syncFileChanges(item, parentFolderID, driveID, syncRootPath, drivePath, newFiles)

		if newFiles:
			self._syncFileAdditions(newFiles, syncRootPath, driveID)

			if self.settings.getSetting("update_library"):
				xbmc.executebuiltin(f"UpdateLibrary(video,{syncRootPath})")

		if self.deleted and self.settings.getSetting("update_library"):

			if os.name == "nt":
				syncRootPath = syncRootPath.replace("\\", "\\\\")

			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.Clean", "params": {"showdialogs": false, "content": "video", "directory": "%s"}}' % syncRootPath)

		self.cache.updateDrive({"page_token": pageToken}, driveID)

	def syncFolderAdditions(self, syncRootPath, drivePath, folder, folderSettings, progressDialog=None, syncedIDs=None):
		syncRootPath = syncRootPath + os.sep
		excludedTypes = getExcludedTypes(folderSettings)
		driveID = folderSettings["drive_id"]
		rootFolderID = folderSettings["folder_id"]
		folderRestructure = folderSettings["folder_restructure"]
		fileRenaming = folderSettings["file_renaming"]
		threadCount = self.settings.getSettingInt("thread_count", 1)

		if folderSettings["contains_encrypted"]:
			encryptor = self.encryptor
		else:
			encryptor = None

		fileTree = FileTree(self.cloudService, self.cache, driveID, drivePath, progressDialog, threadCount, encryptor, excludedTypes, syncedIDs)
		fileTree.buildTree(folder)

		with ThreadPool(threadCount) as pool:

			for folder in fileTree:
				directory = {
					"drive_id": driveID,
					"folder_id": folder.id,
					"local_path": folder.remotePath,
					"remote_name": folder.name,
					"parent_folder_id": folder.parentID,
					"root_folder_id": rootFolderID,
				}
				self.cache.addDirectory(directory)
				pool.submit(self.remoteFileProcessor.processFiles, folder, folderSettings, syncRootPath, driveID, rootFolderID, threadCount, progressDialog)

		if progressDialog:
			progressDialog.processFolder()

		if folderRestructure or fileRenaming:

			with ThreadPool(threadCount) as pool:

				for folder in fileTree:
					pool.submit(self.localFileProcessor.processFiles, folder, folderSettings, syncRootPath, threadCount, progressDialog)

		for folder in fileTree:
			modifiedTime = folder.modifiedTime

			try:
				os.utime(folder.localPath, (modifiedTime, modifiedTime))
			except os.error:
				continue

	def _syncFileAdditions(self, files, syncRootPath, driveID):
		syncRootPath = syncRootPath + os.sep
		threadCount = self.settings.getSettingInt("thread_count", 1)
		folders = []

		with ThreadPool(threadCount) as pool:

			for rootFolderID, directories in files.items():
				folderSettings = self.cache.getFolder({"folder_id": rootFolderID})
				folderRestructure = folderSettings["folder_restructure"]
				fileRenaming = folderSettings["file_renaming"]

				for folderID, folder in directories.items():
					pool.submit(self.remoteFileProcessor.processFiles, folder, folderSettings, syncRootPath, driveID, rootFolderID, threadCount)

					if folderRestructure or fileRenaming:
						folders.append((folder, folderSettings))

		with ThreadPool(threadCount) as pool:

			for folder, folderSettings in folders:
				pool.submit(self.localFileProcessor.processFiles, folder, folderSettings, syncRootPath, threadCount)

	def _syncDeletions(self, item, syncRootPath, drivePath):
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
				dirPath = os.path.join(drivePath, cachedDirectory["local_path"])
				self.fileOperations.deleteFile(syncRootPath, dirPath, cachedFile["local_name"])
			else:
				filePath = os.path.join(syncRootPath, cachedFile["local_path"])
				self.fileOperations.deleteFile(syncRootPath, filePath=filePath)

		if not cachedFiles:
			cachedDirectory = self.cache.getDirectory({"folder_id": folderID})

			if not cachedDirectory:
				return

			self.cache.removeEmptyDirectories(cachedDirectory["root_folder_id"])

		self.deleted = True

	def _syncFileChanges(self, file, parentFolderID, driveID, syncRootPath, drivePath, newFiles):
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
				# file has moved outside of root folder hierarchy/tree > delete file
				cachedParentFolderID = cachedFile["parent_folder_id"]
				cachedDirectory = self.cache.getDirectory({"folder_id": cachedParentFolderID})

				if cachedFile["original_folder"]:
					cachedFilePath = os.path.join(drivePath, cachedDirectory["local_path"], cachedFile["local_name"])
				else:
					cachedFilePath = os.path.join(syncRootPath, cachedFile["local_path"])

				self.fileOperations.deleteFile(syncRootPath, filePath=cachedFilePath)
				self.cache.deleteFile(fileID)
				self.deleted = True
				return

			if not rootFolderID:
				return

			folderName = os.path.basename(dirPath)
			dirPath = self.cache.getUniqueDirectoryPath(driveID, dirPath)
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
		excludedTypes = getExcludedTypes(folderSettings)

		if folderSettings["contains_encrypted"]:
			encryptor = self.encryptor
		else:
			encryptor = None

		file = makeFile(file, excludedTypes, encryptor)

		if not file:
			return

		filename = file.name

		if cachedFile:
			cachedParentFolderID = cachedFile["parent_folder_id"]
			cachedDirectory = self.cache.getDirectory({"folder_id": cachedParentFolderID})
			cachedDirPath = cachedDirectory["local_path"]
			rootFolderID = cachedDirectory["root_folder_id"]

			if cachedFile["original_folder"]:
				cachedFilePath = os.path.join(drivePath, cachedDirPath, cachedFile["local_name"])
			else:
				cachedFilePath = os.path.join(syncRootPath, cachedFile["local_path"])

			if cachedFile["remote_name"] == filename and cachedDirPath == dirPath:
				# file contents modified > redownload file

				# GDrive creates a change after a newly uploaded vids metadata has been processed
				if file.type == "video" and file.duration and file.videoWidth and file.videoHeight:
					file.updateDBdata = True

				self.fileOperations.deleteFile(syncRootPath, filePath=cachedFilePath)
				self.cache.deleteFile(fileID)
				self.deleted = True
			elif not cachedFile["original_name"] or not cachedFile["original_folder"] or not os.path.exists(cachedFilePath):
				# new filename needs to be processed or file not existent > redownload file
				self.fileOperations.deleteFile(syncRootPath, filePath=cachedFilePath)
				self.cache.deleteFile(fileID)
				self.deleted = True
			else:
				# file either moved or renamed
				newFilename = file.basename + os.path.splitext(cachedFile["local_name"])[1]

				if cachedFile["original_folder"]:
					dirPath = os.path.join(drivePath, dirPath)
					newFilePath = self.fileOperations.renameFile(syncRootPath, cachedFilePath, dirPath, newFilename)
				else:
					newFilePath = self.fileOperations.renameFile(syncRootPath, cachedFilePath, os.path.dirname(cachedFilePath), newFilename)
					cachedFile["local_path"] = newFilePath

				cachedFile["local_name"] = os.path.basename(newFilePath)
				cachedFile["remote_name"] = filename
				cachedFile["parent_folder_id"] = parentFolderID
				self.cache.updateFile(cachedFile, fileID)
				return

		folder = newFiles.setdefault(rootFolderID, {}).setdefault(parentFolderID, Folder(parentFolderID, parentFolderID, dirPath, dirPath, os.path.join(drivePath, dirPath)))
		files = folder.files

		if file.type in MEDIA_ASSETS:
			files["media_assets"].setdefault(file.ptnName, []).append(file)
		else:
			files[file.type].append(file)

	def _syncFolderChanges(self, folder, parentFolderID, driveID, syncRootPath, drivePath, syncedIDs):
		folderID = folder["id"]
		folderName = folder["name"]
		cachedDirectory = self.cache.getDirectory({"folder_id": folderID})

		if not cachedDirectory:
			# new folder added
			dirPath, rootFolderID = self.cloudService.getDirectory(self.cache, folderID)

			if not rootFolderID:
				return

			folderSettings = self.cache.getFolder({"folder_id": rootFolderID})
			modifiedTime = folder["modifiedTime"]
			dirPath = self.cache.getUniqueDirectoryPath(driveID, dirPath)
			folder = Folder(folderID, parentFolderID, folderName, dirPath, os.path.join(drivePath, dirPath), modifiedTime=modifiedTime)
			self.syncFolderAdditions(syncRootPath, drivePath, folder, folderSettings, syncedIDs=syncedIDs)
			return

		# existing folder
		cachedDirectoryPath = cachedDirectory["local_path"]
		cachedParentFolderID = cachedDirectory["parent_folder_id"]
		cachedRootFolderID = cachedDirectory["root_folder_id"]
		cachedRemoteName = cachedDirectory["remote_name"]

		if parentFolderID != cachedParentFolderID and folderID != cachedRootFolderID:
			# folder has been moved into another directory
			dirPath, rootFolderID = self.cloudService.getDirectory(self.cache, folderID)

			if not dirPath:
				# folder has moved outside of root folder hierarchy/tree > delete folder
				self.cache.removeDirectory(syncRootPath, drivePath, folderID)
				self.deleted = True
			else:
				self.cache.updateDirectory({"parent_folder_id": parentFolderID}, folderID)
				cachedParentDirectory = self.cache.getDirectory({"folder_id": parentFolderID})

				if cachedParentDirectory:
					dirPath = self.cache.getUniqueDirectoryPath(driveID, dirPath)
				else:
					parentDirPath = os.path.split(dirPath)[0]
					parentFolderName = os.path.basename(parentDirPath)
					parentDirPath = self.cache.getUniqueDirectoryPath(driveID, parentDirPath)
					dirPath = os.path.join(parentDirPath, folderName)
					dirPath = self.cache.getUniqueDirectoryPath(driveID, dirPath)
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

				oldPath = os.path.join(drivePath, cachedDirectoryPath)
				newPath = os.path.join(drivePath, dirPath)
				self.fileOperations.renameFolder(syncRootPath, oldPath, newPath)
				self.cache.updateChildPaths(cachedDirectoryPath, dirPath, folderID)

		elif cachedRemoteName != folderName:
			# folder renamed
			cachedDirectoryPathHead, _ = os.path.split(cachedDirectoryPath)
			newDirectoryPath = newDirectoryPath_ = os.path.join(cachedDirectoryPathHead, folderName)
			newDirectoryPath = self.cache.getUniqueDirectoryPath(driveID, newDirectoryPath, folderID)
			oldPath = os.path.join(drivePath, cachedDirectoryPath)
			newPath = os.path.join(drivePath, newDirectoryPath)
			self.fileOperations.renameFolder(syncRootPath, oldPath, newPath)
			self.cache.updateChildPaths(cachedDirectoryPath, newDirectoryPath, folderID)
			self.cache.updateDirectory({"remote_name": folderName}, folderID)

			if folderID == cachedRootFolderID:
				self.cache.updateFolder({"local_path": newDirectoryPath, "remote_name": folderName}, folderID)

	def _sortChanges(self, changes):
		trashed, existingFolders, newFolders, files = [], [], [], []

		for change in changes:
			item = change["file"]

			if item["trashed"]:
				trashed.append(item)
				continue

			item["name"] = removeProhibitedFSchars(item["name"])

			if item["mimeType"] == "application/vnd.google-apps.folder":
				cachedDirectory = self.cache.getDirectory({"folder_id": item["id"]})

				if cachedDirectory:
					existingFolders.append(item)
				else:
					newFolders.append(item)

			else:
				files.append(item)

		return trashed + existingFolders + newFolders + files

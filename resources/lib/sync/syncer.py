import os
import time

from helpers import rpc
from .sync_cache_updater import SyncCacheUpdater
from ..filesystem.folder import Folder
from ..filesystem.file_tree import FileTree
from ..filesystem.file_maker import makeFile
from ..filesystem.fs_constants import MEDIA_ASSETS
from ..filesystem.fs_helpers import getExcludedTypes, removeProhibitedFSchars
from ..filesystem.file_processor import LocalFileProcessor, RemoteFileProcessor
from ..threadpool.threadpool import ThreadPool
from ..encryption.encryption import EncryptionHandler


class Syncer:

	def __init__(self, accountManager, cloudService, fileOperations, settings, cache):
		self.accountManager = accountManager
		self.cloudService = cloudService
		self.fileOperations = fileOperations
		self.settings = settings
		self.cache = cache
		self.encryptor = EncryptionHandler()

	def syncChanges(self, driveID):
		self.accountManager.setAccounts()
		account = self.accountManager.getAccount(driveID)

		if not account:
			return

		self.cloudService.setAccount(account)
		self.cloudService.refreshToken()
		driveSettings = self.cache.getDrive(driveID)
		syncRootPath = self.cache.getSyncRootPath()
		drivePath = os.path.join(syncRootPath, driveSettings["local_path"])
		changes, pageToken = self.cloudService.getChanges(driveSettings["page_token"])

		if not pageToken:
			return

		if not changes:
			self.cache.updateDrive({"last_sync": time.time()}, driveID)
			return True

		changes = self._sortChanges(changes)
		syncedIDs, excludedIDs = [], []
		newFiles = {}
		pathsToClean = set()
		self.deletedStrm = False

		for item in changes:
			id = item["id"]

			if id in syncedIDs:
				continue

			syncedIDs.append(id)

			if item["trashed"]:
				self._syncDeletions(item, syncRootPath, drivePath, pathsToClean)
				continue

			if item["mimeType"] == "application/vnd.google-apps.folder":
				self._syncFolderChanges(item, driveID, syncRootPath, drivePath, syncedIDs, excludedIDs)
			else:
				self._syncFileChanges(item, driveID, syncRootPath, drivePath, newFiles, excludedIDs)

		if self.deletedStrm and self.settings.getSetting("clean_library"):
			videoSource = self.settings.getSetting("video_source")

			if not videoSource:
				videoSource = syncRootPath

			query = {
				"method": "VideoLibrary.Clean",
				"params": {"showdialogs": self.settings.getSetting("clean_library_dialog"), "content": "video", "directory": videoSource},
			}
			rpc(query)

		if newFiles:
			self._syncFileAdditions(newFiles, syncRootPath)

			if self.settings.getSetting("update_library"):
				query = {
					"method": "VideoLibrary.Scan",
					"params": {"showdialogs": self.settings.getSetting("update_library_dialog"), "directory": syncRootPath},
				}
				rpc(query)

		threadCount = self.settings.getSettingInt("thread_count", 1)

		with ThreadPool(threadCount) as pool:
			[pool.submit(self.cache.removeEmptyDirectories, dir) for dir in pathsToClean]

		self.cache.updateDrive({"page_token": pageToken, "last_sync": time.time()}, driveID)
		return True

	def syncFolderAdditions(self, syncRootPath, drivePath, folder, folderSettings, progressDialog=None, syncedIDs=None):
		syncRootPath = syncRootPath + os.sep
		excludedTypes = getExcludedTypes(folderSettings)
		driveID = folderSettings["drive_id"]
		folderRenaming = folderSettings["folder_renaming"]
		fileRenaming = folderSettings["file_renaming"]
		prefix = [p for p in folderSettings["strm_prefix"].split(", ") if p]
		suffix = [s for s in folderSettings["strm_suffix"].split(", ") if s]
		threadCount = self.settings.getSettingInt("thread_count", 1)
		encryptionID = folderSettings["encryption_id"]

		if encryptionID:
			encryptor = self.encryptor if self.encryptor.setEncryptor(encryptionID) else None
		else:
			encryptor = None

		cacheUpdater = SyncCacheUpdater(self.cache)

		with RemoteFileProcessor(self.fileOperations, cacheUpdater, threadCount, progressDialog) as fileProcessor:
			fileTree = FileTree(fileProcessor, self.cloudService, self.cache, cacheUpdater, driveID, syncRootPath, drivePath, folderRenaming, fileRenaming, threadCount, encryptor, prefix, suffix, excludedTypes, syncedIDs)
			fileTree.buildTree(folder)

		if progressDialog:
			progressDialog.processFolder()

		if folderRenaming or fileRenaming:
			localFileProcessor = LocalFileProcessor(self.fileOperations, self.cache, syncRootPath, progressDialog)

			with ThreadPool(threadCount) as pool:
				[pool.submit(localFileProcessor.processFiles, folder, folderSettings, threadCount) for folder in fileTree]

		for folder in fileTree:
			modifiedTime = folder.modifiedTime

			try:
				os.utime(folder.localPath, (modifiedTime, modifiedTime))
			except os.error:
				continue

	def _sortChanges(self, changes):
		trashed, existingFolders, newFolders, files = [], [], [], []

		for change in changes:
			id = change["fileId"]

			if change["changeType"] != "file":
				continue

			if change["removed"]:

				if self.cache.getDirectory({"folder_id": id}) or self.cache.getFolder({"folder_id": id}):
					item = {"mimeType": "application/vnd.google-apps.folder"}
				elif self.cache.getFile({"file_id": id}):
					item = {"mimeType": "file"}
				else:
					continue

				item.update({"id": id, "trashed": True})
				trashed.append(item)
				continue

			item = change["file"]
			item["id"] = id

			try:
				# shared items that google automatically adds to an account don't have parentFolderIDs
				item["parents"] = item["parents"][0]
			except KeyError:
				continue

			if item["trashed"]:
				trashed.append(item)
				continue

			if item["mimeType"] == "application/vnd.google-apps.folder":
				cachedDirectory = self.cache.getDirectory({"folder_id": id})

				if cachedDirectory:
					existingFolders.append(item)
				else:
					newFolders.append(item)

			else:
				files.append(item)

		return trashed + existingFolders + newFolders + files

	def _syncDeletions(self, item, syncRootPath, drivePath, pathsToClean):
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
				filename = cachedFile["local_name"]
				self.deletedStrm = filename.endswith(".strm")
				self.fileOperations.deleteFile(syncRootPath, dirPath, filename)
			else:
				filePath = os.path.join(syncRootPath, cachedFile["local_path"])
				self.deletedStrm = filePath.endswith(".strm")
				self.fileOperations.deleteFile(syncRootPath, filePath=filePath)

		if not cachedFiles:
			cachedDirectory = self.cache.getDirectory({"folder_id": folderID})

			if cachedDirectory:
				pathsToClean.add(cachedDirectory["root_folder_id"])

	def _syncFileAdditions(self, files, syncRootPath):
		syncRootPath = syncRootPath + os.sep
		threadCount = self.settings.getSettingInt("thread_count", 1)
		cacheUpdater = SyncCacheUpdater(self.cache)
		folders = []

		with RemoteFileProcessor(self.fileOperations, cacheUpdater, threadCount) as fileProcessor:

			for rootFolderID, directories in files.items():
				folderSettings = self.cache.getFolder({"folder_id": rootFolderID})
				folderRenaming = folderSettings["folder_renaming"]
				fileRenaming = folderSettings["file_renaming"]
				encryptionID = folderSettings["encryption_id"]

				if encryptionID:
					encryptor = EncryptionHandler()
					encryptor = encryptor if encryptor.setEncryptor(encryptionID) else None
				else:
					encryptor = None

				for folderID, folder in directories.items():

					for files in folder.files.values():
						[fileProcessor.addFile((file, folder, encryptor)) for file in files]

					if folderRenaming or fileRenaming:
						folders.append((folder, folderSettings))

		with ThreadPool(threadCount) as pool:
			localFileProcessor = LocalFileProcessor(self.fileOperations, self.cache, syncRootPath)
			[pool.submit(localFileProcessor.processFiles, folder, folderSettings, threadCount) for folder, folderSettings in folders]

	def _syncFileChanges(self, file, driveID, syncRootPath, drivePath, newFiles, excludedIDs):
		fileID = file["id"]
		parentFolderID = file["parents"]
		cachedDirectory = self.cache.getDirectory({"folder_id": parentFolderID})
		cachedFile = self.cache.getFile({"file_id": fileID})

		if cachedDirectory:
			dirPath = cachedDirectory["local_path"]
			cachedParentFolderID = cachedDirectory["parent_folder_id"]
			rootFolderID = cachedDirectory["root_folder_id"]
		else:
			dirPath, rootFolderID = self.cloudService.getDirectory(self.cache, parentFolderID, self.encryptor, excludedIDs)

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
				self.deletedStrm = cachedFilePath.endswith(".strm")
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
		folderRenaming = folderSettings["folder_renaming"]
		prefix = [p for p in folderSettings["strm_prefix"].split(", ") if p]
		suffix = [s for s in folderSettings["strm_suffix"].split(", ") if s]
		encryptionID = folderSettings["encryption_id"]

		if encryptionID:
			encryptor = self.encryptor if self.encryptor.setEncryptor(encryptionID) else None
		else:
			encryptor = None

		file = makeFile(file, excludedTypes, prefix, suffix, encryptor)

		if not file:
			return

		filename = file.remoteName

		if cachedFile:
			cachedDirectory = self.cache.getDirectory({"folder_id": cachedFile["parent_folder_id"]})
			cachedDirPath = cachedDirectory["local_path"]
			rootFolderID = cachedDirectory["root_folder_id"]

			if cachedFile["original_folder"]:
				cachedFilePath = os.path.join(drivePath, cachedDirPath, cachedFile["local_name"])
			else:
				cachedFilePath = os.path.join(syncRootPath, cachedFile["local_path"])

			if cachedFile["remote_name"] == filename and cachedDirPath == dirPath:
				modifiedTime = file.modifiedTime

				if file.type == "video":

					if cachedFile["has_metadata"] and modifiedTime == cachedFile["modified_time"]:
						return
					elif file.metadata.get("video_duration"):
						# GDrive creates a change after a newly uploaded vids metadata has been processed
						file.updateDB = True

				elif modifiedTime == cachedFile["modified_time"]:
					return

				# file contents modified > redownload file
				self.fileOperations.deleteFile(syncRootPath, filePath=cachedFilePath)
				self.cache.deleteFile(fileID)
			elif not cachedFile["original_name"] or not cachedFile["original_folder"] or not os.path.exists(cachedFilePath):
				# new filename needs to be processed or file not existent > redownload file
				self.fileOperations.deleteFile(syncRootPath, filePath=cachedFilePath)
				self.cache.deleteFile(fileID)
				self.deletedStrm = cachedFilePath.endswith(".strm")
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

		folder = newFiles.setdefault(rootFolderID, {}).setdefault(parentFolderID, Folder(parentFolderID, parentFolderID, rootFolderID, driveID, dirPath, dirPath, os.path.join(drivePath, dirPath), syncRootPath, folderRenaming))
		files = folder.files

		if file.type in MEDIA_ASSETS:
			files["media_asset"].append(file)
		else:
			files[file.type].append(file)

	def _syncFolderChanges(self, folder, driveID, syncRootPath, drivePath, syncedIDs, excludedIDs):
		folderID = folder["id"]
		folderName = folder["name"]
		parentFolderID = folder["parents"]
		cachedDirectory = self.cache.getDirectory({"folder_id": folderID})

		if not cachedDirectory:
			# new folder added
			dirPath, rootFolderID = self.cloudService.getDirectory(self.cache, folderID, self.encryptor, excludedIDs)

			if not rootFolderID:
				return

			folderSettings = self.cache.getFolder({"folder_id": rootFolderID})
			encryptionID = folderSettings["encryption_id"]

			if encryptionID:
				encryptorSet = self.encryptor.setEncryptor(encryptionID)

				if encryptorSet:
					folderName = removeProhibitedFSchars(self.encryptor.decryptDirName(folderName))

			dirPath = self.cache.getUniqueDirectoryPath(driveID, dirPath)
			folder = Folder(folderID, parentFolderID, rootFolderID, driveID, folderName, dirPath, os.path.join(drivePath, dirPath), syncRootPath, folderSettings["folder_renaming"], modifiedTime=folder["modifiedTime"])
			self.syncFolderAdditions(syncRootPath, drivePath, folder, folderSettings, syncedIDs=syncedIDs)
			return

		# existing folder
		cachedDirectoryPath = cachedDirectory["local_path"]
		cachedParentFolderID = cachedDirectory["parent_folder_id"]
		cachedRootFolderID = cachedDirectory["root_folder_id"]
		cachedRemoteName = cachedDirectory["remote_name"]
		folderSettings = self.cache.getFolder({"folder_id": cachedRootFolderID})
		encryptionID = folderSettings["encryption_id"]

		if encryptionID:
			encryptorSet = self.encryptor.setEncryptor(encryptionID)

			if encryptorSet:
				folderName = removeProhibitedFSchars(self.encryptor.decryptDirName(folderName))

		if parentFolderID != cachedParentFolderID and folderID != cachedRootFolderID:
			# folder has been moved into another directory
			dirPath, rootFolderID = self.cloudService.getDirectory(self.cache, folderID, self.encryptor, excludedIDs)

			if not dirPath:
				# folder has moved outside of root folder hierarchy/tree > delete folder
				self.cache.removeDirectory(syncRootPath, drivePath, folderID)
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
			newDirectoryPath = os.path.join(cachedDirectoryPathHead, folderName)
			newDirectoryPath = self.cache.getUniqueDirectoryPath(driveID, newDirectoryPath, folderID)
			oldPath = os.path.join(drivePath, cachedDirectoryPath)
			newPath = os.path.join(drivePath, newDirectoryPath)
			self.fileOperations.renameFolder(syncRootPath, oldPath, newPath)
			self.cache.updateChildPaths(cachedDirectoryPath, newDirectoryPath, folderID)
			self.cache.updateDirectory({"remote_name": folderName}, folderID)

			if folderID == cachedRootFolderID:
				self.cache.updateFolder({"local_path": newDirectoryPath, "remote_name": folderName}, folderID)

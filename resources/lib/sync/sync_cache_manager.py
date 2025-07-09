import os

from constants import *
from ..database.db_manager import DatabaseManager
from ..ui.dialogs import Dialog, FileDeletionDialog
from ..filesystem.file_operations import FileOperations

if not os.path.exists(ADDON_PATH):
	os.mkdir(ADDON_PATH)

CACHE_PATH = os.path.join(ADDON_PATH, "sync_cache.db")


class SyncCacheManager(DatabaseManager):

	def __init__(self):
		newDB = not os.path.exists(CACHE_PATH)
		super().__init__(CACHE_PATH)
		self.settings = SETTINGS
		self.fileOperations = FileOperations()

		if newDB:
			self.createTables()

	def addDirectories(self, values):
		columns = (
			"drive_id",
			"root_folder_id",
			"parent_folder_id",
			"folder_id",
			"local_path",
			"remote_name",
		)
		self.insertMany("directories", columns, values)

	def addDirectory(self, data):
		self.insert("directories", data)

	def addDrive(self, data):
		self.insert("drives", data)

	def addFile(self, data):
		self.insert("files", data)

	def addFiles(self, values):
		columns = (
			"drive_id",
			"root_folder_id",
			"parent_folder_id",
			"file_id",
			"local_path",
			"local_name",
			"remote_name",
			"original_name",
			"original_folder",
			"has_metadata",
			"modified_time",
		)
		self.insertMany("files", columns, values)

	def addFolder(self, data):
		self.insert("folders", data)

	def addFolders(self, values):
		columns = (
			"drive_id",
			"folder_id",
			"local_path",
			"remote_name",
			"encryption_id",
			"strm_prefix",
			"strm_suffix",
			"file_renaming",
			"folder_renaming",
			"sync_nfo",
			"sync_subtitles",
			"sync_artwork",
			"sync_strm",
			"tmdb_language",
			"tmdb_region",
			"tmdb_adult",
		)
		self.insertMany("folders", columns, values)

	def addGlobalData(self, data):
		self.insert("global", data)

	def createTables(self):
		self._createGlobalTable()
		self._createDriveTable()
		self._createFoldersTable()
		self._createDirectoriesTable()
		self._createFilesTable()

	def deleteDirectory(self, value, column="folder_id"):
		self.delete("directories", {column: value})

	def deleteDrive(self, driveID):
		self.delete("drives", {"drive_id": driveID})

	def deleteFile(self, value, column="file_id"):
		self.delete("files", {column: value})

	def deleteFolder(self, value, column="folder_id"):
		self.delete("folders", {column: value})

	def getDirectories(self, condition, column="*"):
		return self.select("directories", column, condition)

	def getDirectory(self, condition, column="*", caseSensitive=True):
		return self.select("directories", column, condition, caseSensitive, fetchAll=False)

	def getDrive(self, driveID, column="*"):
		return self.select("drives", column, {"drive_id": driveID}, fetchAll=False)

	def getDrives(self):
		return self.select("drives")

	def getFile(self, condition, column="*"):
		return self.select("files", column, condition, fetchAll=False)

	def getFileCount(self, data):
		return self.count("files", data)

	def getFiles(self, condition, column="*"):
		return self.select("files", column, condition)

	def getFolder(self, condition, column="*"):
		return self.select("folders", column, condition, fetchAll=False)

	def getFolders(self, condition, column="*", caseSensitive=True):
		return self.select("folders", column, condition, caseSensitive)

	def getLastSync(self, driveID):
		return self.select("drives", "last_sync", {"drive_id": driveID}, fetchAll=False)

	def getSyncRootPath(self):
		return self.select("global", "local_path", fetchAll=False)

	def getTable(self):
		return self.select("sqlite_master", "name", {"type": "table", "name": "global"}, fetchAll=False)

	def getUniqueDirectoryPath(self, driveID, path, folderID=None, paths=None):
		path_ = path
		copy = 1

		while True:
			cachedFolderID = self.getDirectory({"drive_id": driveID, "local_path": path}, column="folder_id", caseSensitive=False)

			if not cachedFolderID or folderID == cachedFolderID:
				break

			path = f"{path_} ({copy})"
			copy += 1

			if paths:
				paths.add(path.lower())

		return path

	def getUniqueFolderPath(self, driveID, path):
		path_ = path
		copy = 1

		while self.getFolders({"drive_id": driveID, "local_path": path}, caseSensitive=False):
			path = f"{path_} ({copy})"
			copy += 1

		return path

	def removeDirectory(self, syncRootPath, drivePath, folderID):
		directories = self.getDirectories({"folder_id": folderID})

		while directories:
			directory = directories.pop()
			folderID = directory["folder_id"]
			files = self.getFiles({"parent_folder_id": folderID})

			for file in files:

				if file["original_folder"]:
					filePath = os.path.join(drivePath, directory["local_path"], file["local_name"])
				else:
					filePath = os.path.join(syncRootPath, file["local_path"])

				self.fileOperations.deleteFile(syncRootPath, filePath=filePath)

			self.deleteFile(folderID, column="parent_folder_id")
			self.deleteDirectory(folderID)
			directories += self.getDirectories({"parent_folder_id": folderID})

	def removeEmptyDirectories(self, folderID):
		directories = self.getDirectories({"root_folder_id": folderID})
		directories = sorted([(d["local_path"], d["folder_id"]) for d in directories], key=lambda x: -x[0].count(os.sep))
		paths = set(path for path, _ in directories)

		for dirPath, folderID in directories:

			if self.getFile({"parent_folder_id": folderID}):
				continue

			head = dirPath + os.sep

			if not any(path.startswith(head) for path in paths):
				self.deleteDirectory(folderID)
				paths.remove(dirPath)

	def removeFolders(self, driveID=None, folders=None):

		if folders:
			[self._clearCache(folderID=folder["folder_id"]) for folder in folders]
		else:
			self._clearCache(driveID=driveID)

	def removeFoldersAndFiles(self, driveID, folders=None):

		if folders:
			deleteAllfolders = False
			[self.deleteFolder(folder["folder_id"]) for folder in folders]
		else:
			deleteAllfolders = True
			folders = self.getFolders({"drive_id": driveID})

			if not folders:
				return

			self.deleteFolder(driveID, column="drive_id")

		drive = self.getDrive(driveID)
		syncRootPath = self.getSyncRootPath()
		drivePath = os.path.join(syncRootPath, drive["local_path"])

		if not self.settings.getSetting("file_deletion_dialog"):
			dialog = Dialog()
			dialog.notification(30075)
			progressDialog = None
		else:

			if deleteAllfolders:
				fileTotal = self.getFileCount({"drive_id": driveID})
			else:
				fileTotal = sum(self.getFileCount({"root_folder_id": folder["folder_id"]}) for folder in folders)

			progressDialog = FileDeletionDialog(fileTotal)
			progressDialog.create()

		[self._removeDirectories(syncRootPath, drivePath, folder["folder_id"], progressDialog) for folder in folders]

		if progressDialog:
			progressDialog.close()
		else:
			dialog.notification(30045)

	def setSyncRootPath(self, path):
		self.insert("global", {"local_path": path})

	def updateChildPaths(self, oldPath, newPath, folderID):
		directories = self.getDirectories({"folder_id": folderID})
		processedIDs = set()

		while directories:
			directory = directories.pop()
			folderID = directory["folder_id"]

			if folderID in processedIDs:
				continue

			processedIDs.add(folderID)
			directory["local_path"] = directory["local_path"].replace(oldPath, newPath, 1)
			self.updateDirectory(directory, folderID)
			directories += self.getDirectories({"parent_folder_id": folderID})

	def updateDirectory(self, data, folderID):
		self.update("directories", data, {"folder_id": folderID})

	def updateDrive(self, data, driveID):
		self.update("drives", data, {"drive_id": driveID})

	def updateFile(self, data, fileID):
		self.update("files", data, {"file_id": fileID})

	def updateFolder(self, data, folderID):
		self.update("folders", data, {"folder_id": folderID})

	def updateSyncRootPath(self, path):
		self.update("global", {"local_path": path})

	def _clearCache(self, driveID=None, folderID=None):

		if driveID:
			self.deleteFile(driveID, column="drive_id")
			self.deleteDirectory(driveID, column="drive_id")
			self.deleteFolder(driveID, column="drive_id")
		else:
			self.deleteFile(folderID, column="root_folder_id")
			self.deleteDirectory(folderID, column="root_folder_id")
			self.deleteFolder(folderID, column="folder_id")

	def _createDirectoriesTable(self):
		columns = (
			"drive_id TEXT",
			"root_folder_id TEXT",
			"parent_folder_id TEXT",
			"folder_id TEXT",
			"local_path TEXT",
			"remote_name TEXT",
		)
		self.createTable("directories", columns)

	def _createDriveTable(self):
		columns = (
			"drive_id TEXT",
			"local_path TEXT",
			"page_token INTEGER",
			"last_sync REAL",
			"task_mode TEXT",
			"task_frequency TEXT",
			"startup_sync INTEGER",
		)
		self.createTable("drives", columns)

	def _createFilesTable(self):
		columns = (
			"drive_id TEXT",
			"root_folder_id TEXT",
			"parent_folder_id TEXT",
			"file_id TEXT",
			"local_path TEXT",
			"local_name TEXT",
			"remote_name TEXT",
			"original_name INTEGER",
			"original_folder INTEGER",
			"has_metadata INTEGER",
			"modified_time INTEGER",
		)
		self.createTable("files", columns)

	def _createFoldersTable(self):
		columns = (
			"drive_id TEXT",
			"folder_id TEXT",
			"local_path TEXT",
			"remote_name TEXT",
			"encryption_id TEXT",
			"strm_prefix TEXT",
			"strm_suffix TEXT",
			"file_renaming INTEGER",
			"folder_renaming INTEGER",
			"sync_nfo INTEGER",
			"sync_subtitles INTEGER",
			"sync_artwork INTEGER",
			"sync_strm INTEGER",
			"tmdb_language TEXT",
			"tmdb_region TEXT",
			"tmdb_adult INTEGER",
		)
		self.createTable("folders", columns)

	def _createGlobalTable(self):
		columns = ("local_path TEXT",)
		self.createTable("global", columns)

	def _removeDirectories(self, syncRootPath, drivePath, rootFolderID, progressDialog):
		directories = self.getDirectories({"root_folder_id": rootFolderID})

		for directory in directories:
			folderID = directory["folder_id"]
			files = self.getFiles({"parent_folder_id": folderID})

			for file in files:

				if file["original_folder"]:
					filename = file["local_name"]
					filePath = os.path.join(drivePath, directory["local_path"], filename)
				else:
					filePath = os.path.join(syncRootPath, file["local_path"])
					filename = os.path.basename(filePath)

				self.fileOperations.deleteFile(syncRootPath, filePath=filePath)

				if progressDialog:
					progressDialog.processed += 1
					progressDialog.update(filename)

		self.deleteFile(rootFolderID, column="root_folder_id")
		self.deleteDirectory(rootFolderID, column="root_folder_id")

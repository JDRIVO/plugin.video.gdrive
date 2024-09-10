import os

import xbmcvfs
import xbmcaddon

from ..ui import dialogs
from ..filesystem import operations
from ..database.database import Database
from constants import settings

ADDON_PATH = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo("profile"))

if not os.path.exists(ADDON_PATH):
	os.mkdir(ADDON_PATH)

CACHE_PATH = os.path.join(ADDON_PATH, "cache.db")


class Cache(Database):

	def __init__(self):
		newDB = not os.path.exists(CACHE_PATH)
		super().__init__(CACHE_PATH)
		self.fileOperations = operations.FileOperations()

		if newDB:
			self._createTables()

	def addDirectories(self, values):
		columns = (
			"drive_id",
			"folder_id",
			"local_path",
			"parent_folder_id",
			"root_folder_id",
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
		)
		self.insertMany("files", columns, values)

	def addFolder(self, data):
		self.insert("folders", data)

	def addGlobalData(self, data):
		self.insert("global", data)

	def cleanCache(self, driveID):
		self.deleteFile(driveID, column="drive_id")
		self.deleteDirectory(driveID, column="drive_id")
		self.deleteFolder(driveID, column="drive_id")

	def deleteDirectory(self, value, column="folder_id"):
		self.delete("directories", {column: value})

	def deleteDrive(self, driveID):
		drive = self.getDrive(driveID)

		if not drive:
			return

		self.cleanCache(driveID)
		self.delete("drives", {"drive_id": driveID})

	def deleteFile(self, value, column="file_id"):
		self.delete("files", {column: value})

	def deleteFolder(self, value, column="folder_id"):
		self.delete("folders", {column: value})

	def getDirectories(self, condition):
		return self.selectAll("directories", condition)

	def getDirectory(self, condition):
		directory = self.selectAll("directories", condition)
		if directory: return directory[0]

	def getDrive(self, driveID):
		drive = self.selectAll("drives", {"drive_id": driveID})
		if drive: return drive[0]

	def getDrives(self):
		drives = self.selectAll("drives")
		return drives

	def getFile(self, condition):
		file = self.selectAll("files", condition)
		if file: return file[0]

	def getFileCount(self, data):
		return self.count("files", data)

	def getFiles(self, condition):
		return self.selectAll("files", condition)

	def getFolder(self, condition):
		folder = self.selectAll("folders", condition)
		if folder: return folder[0]

	def getFolders(self, condition):
		return self.selectAll("folders", condition)

	def getSyncRootPath(self):
		return self.select("global", "local_path")

	def getUniqueDirectoryPath(self, driveID, path, folderID=None, paths=set()):
		path_ = path
		copy = 1

		while True:
			cachedFolderID = self.select("directories", "folder_id", {"drive_id": driveID, "local_path": path}, caseSensitive=False)

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

		while self.selectAll("folders", {"drive_id": driveID, "local_path": path}, caseSensitive=False):
			path = f"{path_} ({copy})"
			copy += 1

		return path

	def removeDirectories(self, syncRootPath, drivePath, rootFolderID, deleteFiles, progressDialog):

		if deleteFiles:
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
		directories = sorted([(dir["local_path"], dir["folder_id"]) for dir in directories], key=lambda x: x[0])

		for idx, (dirPath, folderID) in enumerate(directories):

			for path, id in directories[idx:]:

				if path.startswith(dirPath + os.sep):
					break

			else:
				files = self.getFiles({"parent_folder_id": folderID})

				if not files:
					self.deleteDirectory(folderID)

	def removeFolder(self, folderID, deleteFiles=False):
		folder = self.getFolder({"folder_id": folderID})
		self.deleteFolder(folderID)
		driveID = folder["drive_id"]
		drive = self.getDrive(driveID)
		syncRootPath = self.getSyncRootPath()
		drivePath = os.path.join(syncRootPath, drive["local_path"])
		progressDialog = settings.getSetting("file_deletion_dialog")

		if deleteFiles and progressDialog:
			fileTotal = self.getFileCount({"root_folder_id": folderID})
			progressDialog = dialogs.FileDeletionDialog(fileTotal)
			progressDialog.create()
		else:
			progressDialog = None

		self.removeDirectories(syncRootPath, drivePath, folderID, deleteFiles, progressDialog)

		if progressDialog:
			progressDialog.close()

	def removeFolders(self, driveID, deleteFiles=False):

		if not deleteFiles:
			self.cleanCache(driveID)
			return

		folders = self.getFolders({"drive_id": driveID})
		self.deleteFolder(driveID, column="drive_id")
		drive = self.getDrive(driveID)
		syncRootPath = self.getSyncRootPath()
		drivePath = os.path.join(syncRootPath, drive["local_path"])
		progressDialog = settings.getSetting("file_deletion_dialog")

		if progressDialog:
			fileTotal = self.getFileCount({"drive_id": driveID})
			progressDialog = dialogs.FileDeletionDialog(fileTotal)
			progressDialog.create()

		for folder in folders:
			self.removeDirectories(syncRootPath, drivePath, folder["folder_id"], deleteFiles, progressDialog)

		if progressDialog:
			progressDialog.close()

	def setSyncRootPath(self, path):
		self.insert("global", {"local_path": path})

	def updateChildPaths(self, oldPath, newPath, folderID):
		directories = self.getDirectories({"folder_id": folderID})
		processedIDs = set()

		while directories:
			directory = directories.pop()
			folderID = directory["folder_id"]
			directory["local_path"] = directory["local_path"].replace(oldPath, newPath, 1)
			self.updateDirectory(directory, folderID)

			if folderID in processedIDs:
				continue

			processedIDs.add(folderID)
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
		self.update("global", {"local_path": path}, {"local_path": "TEXT"})

	def _createDirectoriesTable(self):
		columns = [
			"drive_id TEXT",
			"root_folder_id TEXT",
			"parent_folder_id TEXT",
			"folder_id TEXT",
			"local_path TEXT",
			"remote_name TEXT",
		]
		self.createTable("directories", columns)

	def _createDriveTable(self):
		columns = [
			"drive_id TEXT",
			"local_path TEXT",
			"page_token INTEGER",
			"last_update REAL",
			"task_mode TEXT",
			"task_frequency TEXT",
			"startup_sync INTEGER",
		]
		self.createTable("drives", columns)

	def _createFilesTable(self):
		columns = [
			"drive_id TEXT",
			"root_folder_id TEXT",
			"parent_folder_id TEXT",
			"file_id TEXT",
			"local_path TEXT",
			"local_name TEXT",
			"remote_name TEXT",
			"original_name INTEGER",
			"original_folder INTEGER",
		]
		self.createTable("files", columns)

	def _createFoldersTable(self):
		columns = [
			"drive_id TEXT",
			"folder_id TEXT",
			"local_path TEXT",
			"remote_name TEXT",
			"file_renaming INTEGER",
			"folder_restructure INTEGER",
			"contains_encrypted INTEGER",
			"sync_artwork INTEGER",
			"sync_nfo INTEGER",
			"sync_subtitles INTEGER",
			"tmdb_language TEXT",
			"tmdb_region TEXT",
			"tmdb_adult TEXT",
		]
		self.createTable("folders", columns)

	def _createGlobalTable(self):
		columns = [
			"local_path TEXT",
			"operating_system TEXT",
		]
		self.createTable("global", columns)

	def _createTables(self):
		self._createGlobalTable()
		self._createDriveTable()
		self._createFoldersTable()
		self._createDirectoriesTable()
		self._createFilesTable()

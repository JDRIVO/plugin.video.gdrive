import os

import xbmcvfs
import xbmcaddon

from ..ui import dialogs
from constants import settings
from ..filesystem import operations
from ..database.database import Database

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
			self.createTables()

	def updateDrive(self, data, driveID):
		self.update("drives", data, {"drive_id": driveID})

	def updateFile(self, data, fileID):
		self.update("files", data, {"file_id": fileID})

	def updateFolder(self, data, folderID):
		self.update("folders", data, {"folder_id": folderID})

	def updateDirectory(self, data, folderID):
		self.update("directories", data, {"folder_id": folderID})

	def addDrive(self, data):
		self.insert("drives", data)

	def addFolder(self, data):
		self.insert("folders", data)

	def addDirectory(self, data):
		self.insert("directories", data)

	def addDirectories(self, values):
		columns = (
			"drive_id",
			"folder_id",
			"local_path",
			"parent_folder_id",
			"root_folder_id",
		)
		self.insertMany("directories", columns, values)

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

	def getDrives(self):
		drives = self.selectAll("drives")
		return drives

	def getDrive(self, driveID):
		data = {"drive_id": driveID}
		drive = self.selectAllConditional("drives", data)
		if drive: return drive[0]

	def getDirectory(self, data):
		directory = self.selectAllConditional("directories", data)
		if directory: return directory[0]

	def getFolder(self, data):
		folder = self.selectAllConditional("folders", data)
		if folder: return folder[0]

	def getFile(self, data):
		file = self.selectAllConditional("files", data)
		if file: return file[0]

	def getFolders(self, data):
		return self.selectAllConditional("folders", data)

	def getDirectories(self, data):
		return self.selectAllConditional("directories", data)

	def getFiles(self, data):
		return self.selectAllConditional("files", data)

	def deleteFile(self, value, column="file_id"):
		self.delete("files", {column: value})

	def deleteDirectory(self, value, column="folder_id"):
		self.delete("directories", {column: value})

	def deleteFolder(self, value, column="folder_id"):
		self.delete("folders", {column: value})

	def deleteDrive(self, driveID):
		drive = self.getDrive(driveID)

		if not drive:
			return

		self.cleanCache(driveID)
		self.delete("drives", {"drive_id": driveID})

	def removeFolder(self, folderID, deleteFiles=False):
		folder = self.getFolder({"folder_id": folderID})
		self.deleteFolder(folderID)
		driveID = folder["drive_id"]
		drive = self.getDrive(driveID)
		syncRootPath = self.getSyncRootPath()
		drivePath = os.path.join(syncRootPath, drive["local_path"])
		progressDialog = settings.getSetting("file_deletion_dialog")

		if deleteFiles and progressDialog:
			progressDialog = dialogs.FileDeletionDialog(0, heading=settings.getLocalizedString(30075))
		else:
			progressDialog = False

		self.removeDirectories(syncRootPath, drivePath, folderID, deleteFiles, progressDialog)

		if progressDialog:
			progressDialog.close()

	def removeAllFolders(self, driveID, deleteFiles=False):

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
			progressDialog = dialogs.FileDeletionDialog(0, heading=settings.getLocalizedString(30075))

		for folder in folders:
			self.removeDirectories(syncRootPath, drivePath, folder["folder_id"], deleteFiles, progressDialog)

		if progressDialog:
			progressDialog.close()

	def updateSyncRootPath(self, path):
		self.update("global", {"local_path": path}, {"local_path": "TEXT"})

	def setSyncRootPath(self, path):
		self.insert("global", {"local_path": path})

	def getSyncRootPath(self):
		return self.select("global", "local_path")

	def addGlobalData(self, data):
		self.insert("global", data)

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

	def cleanCache(self, driveID):
		self.deleteFile(driveID, column="drive_id")
		self.deleteDirectory(driveID, column="drive_id")
		self.deleteFolder(driveID, column="drive_id")

	def removeDirectories(self, syncRootPath, drivePath, folderID, deleteFiles, progressDialog):
		directories = self.getDirectories({"folder_id": folderID})

		while directories:
			directory = directories.pop()
			folderID = directory["folder_id"]

			if deleteFiles:
				files = self.getFiles({"parent_folder_id": folderID})

				if progressDialog:
					progressDialog.fileCount += len(files)

				for file in files:

					if file["original_folder"]:
						filename = file["local_name"]
						filePath = os.path.join(os.path.join(drivePath, directory["local_path"]), filename)
					else:
						filePath = os.path.join(syncRootPath, file["local_path"])
						filename = os.path.basename(filePath)

					self.fileOperations.deleteFile(syncRootPath, filePath=filePath)

					if progressDialog:
						progressDialog.update(filename)

			self.deleteFile(folderID, column="parent_folder_id")
			self.deleteDirectory(folderID)
			directories += self.getDirectories({"parent_folder_id": folderID})

	def createGlobalTable(self):
		columns = [
			"local_path TEXT",
			"operating_system TEXT",
		]
		self.createTable("global", columns)

	def createDriveTable(self):
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

	def createFoldersTable(self):
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

	def createDirectoriesTable(self):
		columns = [
			"drive_id TEXT",
			"root_folder_id TEXT",
			"parent_folder_id TEXT",
			"folder_id TEXT",
			"local_path TEXT",
			"remote_name TEXT",
		]
		self.createTable("directories", columns)

	def createFilesTable(self):
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

	def createTables(self):
		self.createGlobalTable()
		self.createDriveTable()
		self.createFoldersTable()
		self.createDirectoriesTable()
		self.createFilesTable()

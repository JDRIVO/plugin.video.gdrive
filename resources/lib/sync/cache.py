import os

import xbmcvfs
import xbmcaddon

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
		self.update("drives", data, f"drive_id='{driveID}'")

	def updateFile(self, data, fileID):
		self.update("files", data, f"file_id='{fileID}'")

	def updateFolder(self, data, folderID):
		self.update("folders", data, f"folder_id='{folderID}'")

	def updateDirectory(self, data, folderID):
		self.update("directories", data, f"folder_id='{folderID}'")

	def getDriveSetting(self, column, driveID):
		self.selectConditional("drives", column, f"drive_id='{driveID}'")

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

	def getDrive(self, value, column="drive_id"):
		drive = self.selectAllConditional("drives", f"{column}='{value}'")
		if drive: return drive[0]

	def getDirectory(self, value, column="folder_id"):
		directory = self.selectAllConditional("directories", f"{column}='{value}'")
		if directory: return directory[0]

	def getFolder(self, value, column="folder_id"):
		folder = self.selectAllConditional("folders", f"{column}='{value}'")
		if folder: return folder[0]

	def getFile(self, value, column="file_id"):
		file = self.selectAllConditional("files", f"{column}='{value}'")
		if file: return file[0]

	def getFolders(self, value, column="drive_id"):
		return self.selectAllConditional("directories", f"{column}='{value}'")

	def getDirectories(self, value, column="parent_folder_id"):
		return self.selectAllConditional("directories", f"{column}='{value}'")

	def getFiles(self, value, column="parent_folder_id"):
		return self.selectAllConditional("files", f"{column}='{value}'")

	def deleteFile(self, value, column="file_id"):
		self.delete("files", f"{column}='{value}'")

	def deleteDirectory(self, value, column="folder_id"):
		self.delete("directories", f"{column}='{value}'")

	def deleteFolder(self, value, column="folder_id"):
		self.delete("folders", f"{column}='{value}'")

	def deleteDrive(self, driveID):
		syncRootPath = self.getSyncRootPath()
		drive = self.getDrive(driveID)

		if not drive:
			return

		drivePath = os.path.join(syncRootPath, drive["local_path"])
		folders = self.getFolders(driveID)

		for folder in folders:
			folderID = folder["folder_id"]
			self.cleanCache(syncRootPath, drivePath, folder["folder_id"])

		self.deleteFolder(driveID, "drive_id")
		self.delete("drives", f"drive_id='{driveID}'")

	def updateSyncRootPath(self, path):
		self.update("global", {"local_path": path}, "local_path=TEXT")

	def setSyncRootPath(self, path):
		self.insert("global", {"local_path": path})

	def getSyncRootPath(self):
		return self.select("global", "local_path")

	def addGlobalData(self, data):
		self.insert("global", data)

	def updateChildPaths(self, oldPath, newPath, folderID, directoryColumn="folder_id"):
		directories = self.getDirectories(folderID, directoryColumn)

		if not directories:
			return

		for directory in directories:
			cahedfolderID = directory["folder_id"]
			cachedDirectoryPath = directory["local_path"]
			modifiedPath = cachedDirectoryPath.replace(oldPath, newPath)
			directory["local_path"] = modifiedPath
			self.updateDirectory(directory, cahedfolderID)
			self.updateChildPaths(oldPath, newPath, cahedfolderID, directoryColumn="parent_folder_id")

	def cleanCache(self, syncRootPath, drivePath, folderID, directoryColumn="folder_id"):
		directories = self.getDirectories(folderID, directoryColumn)

		if not directories:
			return

		for directory in directories:
			folderID = directory["folder_id"]
			files = self.getFiles(folderID)

			if files:
				cachedDirectoryPath = directory["local_path"]
				directoryPath = os.path.join(drivePath, cachedDirectoryPath)

				for file in files:

					if file["original_folder"]:
						filePath = os.path.join(directoryPath, file["local_name"])
					else:
						filePath = os.path.join(syncRootPath, file["local_path"])

					self.fileOperations.deleteFile(syncRootPath, filePath=filePath)

			self.deleteFile(folderID, "parent_folder_id")
			self.deleteDirectory(folderID)
			self.cleanCache(syncRootPath, drivePath, folderID, directoryColumn="parent_folder_id")

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
			"file_renaming INTEGER",
			"folder_restructure INTEGER",
			"contains_encrypted INTEGER",
			"sync_artwork INTEGER",
			"sync_nfo INTEGER",
			"sync_subtitles INTEGER",
		]
		self.createTable("folders", columns)

	def createDirectoriesTable(self):
		columns = [
			"drive_id TEXT",
			"root_folder_id TEXT",
			"parent_folder_id TEXT",
			"folder_id TEXT",
			"local_path TEXT",
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

import os
import shutil

from . import helpers


class FileOperations:

	def __init__(self, cloudService, encryption):
		self.cloudService = cloudService
		self.encryption = encryption

	def downloadFiles(self, files, dirPath, cachedFiles, folderID, fileIDs):

		for file in list(files):
			fileID = file.id
			filename = file.name
			encrypted = file.encrypted
			filePath = helpers.generateFilePath(dirPath, filename)

			if encrypted:
				self.downloadFile(dirPath, filePath, fileID, encrypted=True)
			else:
				self.downloadFile(dirPath, filePath, fileID)

			cachedFiles[fileID]  = {
				"local_name": os.path.basename(filePath),
				"remote_name": filename,
				"local_path": False,
				"parent_folder_id": folderID,
				"original_name": True,
				"original_folder": True,
			}

			if fileID not in fileIDs:
				fileIDs.append(fileID)

			files.remove(file)

	def downloadFile(self, dirPath, filePath, fileID, encrypted=False):
		self.createDirs(dirPath)
		file = self.cloudService.downloadFile(fileID)

		if file:

			if encrypted:
				self.encryption.decryptStream(file, filePath)
			else:
				self.createFile(dirPath, filePath, file.read())

	def createFile(self, dirPath, filePath, content, mode="wb"):
		self.createDirs(dirPath)

		with open(filePath, mode) as f:
			f.write(content)

	def deleteFiles(self, syncRoot, folderID, cachedDirectories, cachedFiles):

		if not cachedDirectories.get(folderID):
			return

		cachedDirectory = cachedDirectories[folderID]
		cachedDirPath = cachedDirectory["local_path"]
		folderIDs = cachedDirectory["folder_ids"]
		fileIDs = cachedDirectory["file_ids"]

		for fileID in fileIDs:

			if fileID not in cachedFiles:
				continue

			cachedFile = cachedFiles[fileID]

			if cachedFile["original_folder"]:
				self.deleteFile(syncRoot, dirPath=cachedDirPath, filename=cachedFile["local_name"])
			else:
				self.deleteFile(syncRoot, filePath=cachedFile["local_path"])

			del cachedFiles[fileID]

		for dirID in folderIDs:
			self.deleteFiles(syncRoot, dirID, cachedDirectories, cachedFiles)

		del cachedDirectories[folderID]

	def deleteFile(self, syncRoot, filePath=None, dirPath=None, filename=None):

		if not filePath:
			filePath = os.path.join(dirPath, filename)
		else:
			dirPath, filename = os.path.split(filePath)

		if os.path.exists(filePath):
			os.remove(filePath)

		self.deleteEmptyDirs(dirPath, syncRoot)

	def createDirs(self, dirPath):

		if not os.path.exists(dirPath):
			os.makedirs(dirPath)

	def renameFile(self, syncRoot, oldPath, dirPath, newName):
		self.createDirs(dirPath)
		newPath = helpers.duplicateFileCheck(dirPath, newName)
		shutil.move(oldPath, newPath)
		self.deleteEmptyDirs(os.path.dirname(oldPath), syncRoot)
		return newPath

	def renameFolder(self, syncRoot, oldPath, newPath):

		if os.path.exists(oldPath):
			shutil.move(oldPath, newPath)
			self.deleteEmptyDirs(os.path.dirname(oldPath), syncRoot)

	@staticmethod
	def deleteEmptyDirs(dirPath, syncRoot):

		while dirPath != syncRoot and os.path.exists(dirPath) and not os.listdir(dirPath):
			os.rmdir(dirPath)
			dirPath = dirPath.rsplit(os.sep, 1)[0]

	@staticmethod
	def readFile(path):

		with open(path, "r") as file:
			return file.read()

import os
import shutil
import threading

from . import helpers


class FileOperations:

	def __init__(self, **kwargs):
		self.cloudService = kwargs.get("cloud_service")
		self.encryption = kwargs.get("encryption")
		self.fileLock = threading.Lock()

	def downloadFile(self, dirPath, filename, fileID, modifiedTime=None, encrypted=False):
		self.createDirs(dirPath)
		file = self.cloudService.downloadFile(fileID)

		if file:

			if encrypted:

				with self.fileLock:
					filePath = helpers.generateFilePath(dirPath, filename)
					self.encryption.decryptStream(file, filePath, modifiedTime=modifiedTime)

			else:
				filePath = self.createFile(dirPath, filename, file.read(), modifiedTime=modifiedTime)

			return filePath

	def createFile(self, dirPath, filename, content, modifiedTime=None, mode="wb"):
		self.createDirs(dirPath)

		with self.fileLock:
			filePath = helpers.generateFilePath(dirPath, filename)

			with open(filePath, mode) as file:
				file.write(content)

		if modifiedTime:
			os.utime(filePath, (modifiedTime, modifiedTime))

		return filePath

	def deleteFile(self, syncRootPath, dirPath=None, filename=None, filePath=None):

		if not filePath:
			filePath = os.path.join(dirPath, filename)
		else:
			dirPath, filename = os.path.split(filePath)

		if os.path.exists(filePath):
			os.remove(filePath)

		self.deleteEmptyDirs(syncRootPath, dirPath)

	def createDirs(self, dirPath):

		try:

			if not os.path.exists(dirPath):
				os.makedirs(dirPath)

		except FileExistsError:
			return

	def renameFile(self, syncRootPath, oldPath, dirPath, filename):
		self.createDirs(dirPath)
		creationDate = helpers.getCreationDate(oldPath)

		with self.fileLock:
			newPath = helpers.duplicateFileCheck(dirPath, filename, creationDate)
			shutil.move(oldPath, newPath)

		self.deleteEmptyDirs(syncRootPath, os.path.dirname(oldPath))
		return newPath

	def renameFolder(self, syncRootPath, oldPath, newPath):

		if os.path.exists(oldPath):
			shutil.move(oldPath, newPath)
			self.deleteEmptyDirs(syncRootPath, os.path.dirname(oldPath))

	@staticmethod
	def deleteEmptyDirs(syncRootPath, dirPath):

		try:

			while dirPath != syncRootPath and os.path.exists(dirPath):
				os.rmdir(dirPath)
				dirPath = dirPath.rsplit(os.sep, 1)[0]

		except OSError:
			return

	@staticmethod
	def readFile(filePath):

		with open(filePath, "r") as file:
			return file.read()

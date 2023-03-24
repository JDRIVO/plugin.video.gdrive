import os
import shutil

from . import helpers


class FileOperations:

	def __init__(self, **kwargs):
		self.cloudService = kwargs.get("cloud_service")
		self.encryption = kwargs.get("encryption")

	def downloadFile(self, dirPath, filePath, fileID, modifiedTime=None, encrypted=False):
		self.createDirs(dirPath)
		file = self.cloudService.downloadFile(fileID)

		if file:

			if encrypted:
				self.encryption.decryptStream(file, filePath, modifiedTime=modifiedTime)
			else:
				self.createFile(dirPath, filePath, file.read(), modifiedTime=modifiedTime)

	def createFile(self, dirPath, filePath, content, modifiedTime=None, mode="wb"):
		self.createDirs(dirPath)

		with open(filePath, mode) as file:
			file.write(content)

		if modifiedTime:
			os.utime(filePath, (modifiedTime, modifiedTime))

	def deleteFile(self, syncRootPath, dirPath=None, filename=None, filePath=None):

		if not filePath:
			filePath = os.path.join(dirPath, filename)
		else:
			dirPath, filename = os.path.split(filePath)

		if os.path.exists(filePath):
			os.remove(filePath)

		self.deleteEmptyDirs(syncRootPath, dirPath)

	def createDirs(self, dirPath):

		if not os.path.exists(dirPath):
			os.makedirs(dirPath)

	def renameFile(self, syncRootPath, oldPath, dirPath, newName):

		try:
			self.createDirs(dirPath)
			newPath = helpers.duplicateFileCheck(dirPath, newName)
			shutil.move(oldPath, newPath)
			self.deleteEmptyDirs(syncRootPath, os.path.dirname(oldPath))
			return newPath
		except FileExistsError:
			return

	def renameFolder(self, syncRootPath, oldPath, newPath):

		if os.path.exists(oldPath):
			shutil.move(oldPath, newPath)
			self.deleteEmptyDirs(syncRootPath, os.path.dirname(oldPath))

	@staticmethod
	def deleteEmptyDirs(syncRootPath, dirPath):

		try:

			while dirPath != syncRootPath and os.path.exists(dirPath) and not os.listdir(dirPath):
				os.rmdir(dirPath)
				dirPath = dirPath.rsplit(os.sep, 1)[0]

		except Exception as e:
			return

	@staticmethod
	def readFile(path):

		with open(path, "r") as file:
			return file.read()

	@staticmethod
	def overwriteFile(filePath, content, mode="w+"):
		stInfo = os.stat(filePath)

		with open(filePath, mode) as file:
			file.write(content)

		os.utime(filePath, (stInfo.st_atime, stInfo.st_mtime))

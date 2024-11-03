import os
import pickle
import shutil
import threading

import xbmcvfs

from .fs_helpers import duplicateFileCheck, generateFilePath


class FileOperations:

	def __init__(self, **kwargs):
		self.cloudService = kwargs.get("cloud_service")
		self.encryption = kwargs.get("encryption")
		self.lock = threading.Lock()

	def createDirs(self, dirPath):

		try:

			if not os.path.exists(dirPath):
				os.makedirs(dirPath)

		except FileExistsError:
			return

	def createFile(self, dirPath, filename, content, modifiedTime=None, mode="wb"):
		self.createDirs(dirPath)

		with self.lock:
			filePath = generateFilePath(dirPath, filename)

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

		self._deleteEmptyDirs(syncRootPath, dirPath)

	def downloadFile(self, dirPath, filename, fileID, modifiedTime=None, encrypted=False):
		self.createDirs(dirPath)
		file = self.cloudService.downloadFile(fileID)

		if file:

			if encrypted:

				with self.lock:
					filePath = generateFilePath(dirPath, filename)
					self.encryption.decryptStream(file, filePath, modifiedTime=modifiedTime)

			else:
				filePath = self.createFile(dirPath, filename, file.read(), modifiedTime=modifiedTime)

			return filePath

	@staticmethod
	def loadPickleFile(filePath):

		with xbmcvfs.File(filePath) as file:

			try:
				return pickle.loads(file.readBytes())
			except EOFError:
				return

	@staticmethod
	def readFile(filePath):

		try:

			with open(filePath, "r") as file:
				return file.read()

		except FileNotFoundError:
			return

	def renameFile(self, syncRootPath, oldPath, dirPath, filename):
		self.createDirs(dirPath)

		with self.lock:
			newPath = duplicateFileCheck(dirPath, filename, oldPath)
			shutil.move(oldPath, newPath)

		self._deleteEmptyDirs(syncRootPath, os.path.dirname(oldPath))
		return newPath

	def renameFolder(self, syncRootPath, oldPath, newPath):

		if os.path.exists(oldPath):
			shutil.move(oldPath, newPath)
			self._deleteEmptyDirs(syncRootPath, os.path.dirname(oldPath))

	@staticmethod
	def savePickleFile(data, filePath):

		with xbmcvfs.File(filePath, "wb") as file:
			pickle.dump(data, file)

	def _deleteEmptyDirs(self, syncRootPath, dirPath):

		with self.lock:

			try:

				while dirPath != syncRootPath and os.path.exists(dirPath):
					os.rmdir(dirPath)
					dirPath = dirPath.rsplit(os.sep, 1)[0]

			except OSError:
				return

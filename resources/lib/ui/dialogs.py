import threading

import xbmcgui

import constants


class SyncProgressionDialog(xbmcgui.DialogProgressBG):

	def __init__(self, folderTotal):
		self.folderTotal = folderTotal
		self.lock = threading.Lock()
		self.settings = constants.settings
		self.processedFiles = 0
		self.processedFolders = 0
		self.renamedFiles = 0
		self.fileCount = 0

	def create(self):
		super().create(heading=self.getFolderHeading())

	def getSyncedFilesPercentage(self):

		try:
			return int(self.processedFiles / self.fileCount * 100)
		except:
			return 0

	def getRenamedFilesPercentage(self):

		try:
			return int(self.renamedFiles / self.fileCount * 100)
		except:
			return 0

	def getFolderHeading(self):
		return f"{self.settings.getLocalizedString(30000)}: {self.settings.getLocalizedString(30052)} ({self.processedFolders}/{self.folderTotal})"

	def incrementFile(self):

		with self.lock:
			self.fileCount += 1

	def incrementFiles(self, count):

		if self.processedFolders != self.folderTotal or self.processedFolders == 0:
			return

		with self.lock:
			self.renamedFiles += count
			super().update(self.getRenamedFilesPercentage(), heading=f"{self.settings.getLocalizedString(30000)}: {self.settings.getLocalizedString(30053)}")

	def processRenamedFile(self, filename):

		with self.lock:
			self.renamedFiles += 1

		if self.processedFolders != self.folderTotal or self.processedFolders == 0:
			return

		super().update(self.getRenamedFilesPercentage(), message=filename, heading=f"{self.settings.getLocalizedString(30000)}: {self.settings.getLocalizedString(30053)}")

	def processFolder(self):

		with self.lock:
			self.processedFolders += 1
			super().update(self.getSyncedFilesPercentage(), heading=self.getFolderHeading())

	def processFile(self, filename):

		with self.lock:
			self.processedFiles += 1
			super().update(self.getSyncedFilesPercentage(), message=filename, heading=self.getFolderHeading())

class FileDeletionDialog(xbmcgui.DialogProgressBG):

	def __init__(self, fileTotal):
		self.fileTotal = fileTotal
		self.settings = constants.settings
		self.processed = 0
		self.heading = f"{self.settings.getLocalizedString(30000)}: {self.settings.getLocalizedString(30075)}"

	def getPercentage(self):

		try:
			return int(self.processed / self.fileTotal * 100)
		except:
			return 0

	def create(self):
		super().create(heading=self.heading)

	def update(self, filename):
		super().update(self.getPercentage(), message=filename, heading=self.heading)

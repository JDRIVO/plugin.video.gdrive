import os
import threading

import xbmcgui
import xbmcaddon

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
		super().create(heading=self._getFolderHeading())

	def incrementFile(self):

		with self.lock:
			self.fileCount += 1

	def incrementFiles(self, count):

		if self.processedFolders != self.folderTotal or self.processedFolders == 0:
			return

		with self.lock:
			self.renamedFiles += count
			super().update(self._getRenamedFilesPercentage(), heading=f"{self.settings.getLocalizedString(30000)}: {self.settings.getLocalizedString(30053)}")

	def processFile(self, filename):

		with self.lock:
			self.processedFiles += 1
			super().update(self._getSyncedFilesPercentage(), message=filename, heading=self._getFolderHeading())

	def processFolder(self):

		with self.lock:
			self.processedFolders += 1
			super().update(self._getSyncedFilesPercentage(), heading=self._getFolderHeading())

	def processRenamedFile(self, filename):

		with self.lock:
			self.renamedFiles += 1

		if self.processedFolders != self.folderTotal or self.processedFolders == 0:
			return

		super().update(self._getRenamedFilesPercentage(), message=filename, heading=f"{self.settings.getLocalizedString(30000)}: {self.settings.getLocalizedString(30053)}")

	def _getFolderHeading(self):
		return f"{self.settings.getLocalizedString(30000)}: {self.settings.getLocalizedString(30052)} ({self.processedFolders}/{self.folderTotal})"

	def _getSyncedFilesPercentage(self):

		try:
			return int(self.processedFiles / self.fileCount * 100)
		except:
			return 0

	def _getRenamedFilesPercentage(self):

		try:
			return int(self.renamedFiles / self.fileCount * 100)
		except:
			return 0


class FileDeletionDialog(xbmcgui.DialogProgressBG):

	def __init__(self, fileTotal):
		self.fileTotal = fileTotal
		self.settings = constants.settings
		self.processed = 0
		self.heading = f"{self.settings.getLocalizedString(30000)}: {self.settings.getLocalizedString(30075)}"

	def create(self):
		super().create(heading=self.heading)

	def update(self, filename):
		super().update(self._getPercentage(), message=filename, heading=self.heading)

	def _getPercentage(self):

		try:
			return int(self.processed / self.fileTotal * 100)
		except:
			return 0


class Dialog(xbmcgui.Dialog):

	def __init__(self):
		self.icon = os.path.join(xbmcaddon.Addon().getAddonInfo("path"), "resources", "media", "icon.png")

	def notification(self, heading, message, icon=None, time=5000, sound=True):

		if icon is None:
			icon = self.icon

		super().notification(heading, message, icon, time, sound)

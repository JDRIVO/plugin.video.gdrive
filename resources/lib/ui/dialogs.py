import os
import threading

import xbmcgui
import xbmcaddon

from constants import SETTINGS


class Dialog(xbmcgui.Dialog):

	def __init__(self):
		self.settings = SETTINGS
		self.icon = os.path.join(xbmcaddon.Addon().getAddonInfo("path"), "resources", "media", "icon.png")
		self.heading = self.settings.getLocalizedString(30000)

	def browse(self, type, heading, shares, mask="", useThumbs=False, treatAsFolder=False, defaultt="", enableMultiple=False):
		return super().browse(type, self._resolveHeading(heading), shares, mask, useThumbs, treatAsFolder, defaultt, enableMultiple)

	def input(self, heading, defaultt="", type=xbmcgui.INPUT_ALPHANUM, option=0, autoclose=0):
		return super().input(self._resolveHeading(heading), defaultt, type, option, autoclose)

	def multiselect(self, heading, options, autoclose=0, preselect=None, useDetails=False):
		return super().multiselect(self._resolveHeading(heading), options, autoclose, preselect or [], useDetails)

	def notification(self, message, heading=None, icon=None, time=5000, sound=True):
		heading, message = self._resolve(heading, message)
		super().notification(heading, message, icon or self.icon, time, sound)

	def numeric(self, type, heading, defaultt="", bHiddenInput=False):
		return super().numeric(type, self._resolveHeading(heading), defaultt, bHiddenInput)

	def ok(self, message, heading=None):
		heading, message = self._resolve(heading, message)
		return super().ok(heading, message)

	def select(self, heading, list, autoclose=0, preselect=-1, useDetails=False):
		return super().select(self._resolveHeading(heading), list, autoclose, preselect, useDetails)

	def yesno(self, message, heading=None, nolabel=None, yeslabel=None, autoclose=0, defaultbutton=xbmcgui.DLG_YESNO_NO_BTN):
		heading, message = self._resolve(heading, message)
		return super().yesno(heading, message, nolabel, yeslabel, autoclose, defaultbutton)

	def yesnocustom(self, message, customlabel, heading=None, nolabel=None, yeslabel=None, autoclose=0, defaultbutton=xbmcgui.DLG_YESNO_NO_BTN):
		heading, message = self._resolve(heading, message)
		customlabel = self._resolveMessage(customlabel)
		return super().yesnocustom(heading, message, customlabel, nolabel, yeslabel, autoclose, defaultbutton)

	def _resolve(self, heading, message):
		return self._resolveHeading(heading), self._resolveMessage(message)

	def _resolveHeading(self, heading):

		if heading is None:
			return self.heading
		elif isinstance(heading, int):
			return self.settings.getLocalizedString(heading)
		else:
			return heading

	def _resolveMessage(self, message):
		return self.settings.getLocalizedString(message) if isinstance(message, int) else message


class FileDeletionDialog(xbmcgui.DialogProgressBG):

	def __init__(self, fileTotal):
		self.fileTotal = fileTotal
		self.settings = SETTINGS
		self.processed = 0
		self.heading = f"{self.settings.getLocalizedString(30000)}: {self.settings.getLocalizedString(30075)}"

	def create(self):
		super().create(heading=self.heading)

	def update(self, filename):
		super().update(self._getPercentage(), message=filename, heading=self.heading)

	def _getPercentage(self):

		try:
			return int(self.processed / self.fileTotal * 100)
		except ZeroDivisionError:
			return 0


class SyncProgressionDialog(xbmcgui.DialogProgressBG):

	def __init__(self, folderTotal):
		self.folderTotal = folderTotal
		self.lock = threading.Lock()
		self.settings = SETTINGS
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

	def _getRenamedFilesPercentage(self):

		try:
			return int(self.renamedFiles / self.fileCount * 100)
		except ZeroDivisionError:
			return 0

	def _getSyncedFilesPercentage(self):

		try:
			return int(self.processedFiles / self.fileCount * 100)
		except ZeroDivisionError:
			return 0

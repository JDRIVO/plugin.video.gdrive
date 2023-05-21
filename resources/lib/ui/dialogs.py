import threading

import xbmcgui


class SyncProgressionDialog:

	def __init__(self, fileTree, heading=None, message=None):
		self.pDialog = xbmcgui.DialogProgressBG()
		self.fileTree = fileTree
		self.counterLock = threading.Lock()
		self.processed = 0
		self.pDialog.create(heading, message)

	def close(self):
		self.pDialog.close()

	def update(self, filename):

		with self.counterLock:
			self.processed += 1
			self.pDialog.update(int(self.processed / self.fileTree.fileCount * 100), message=filename)

class FileDeletionDialog:

	def __init__(self, fileCount, heading=None, message=None):
		self.pDialog = xbmcgui.DialogProgressBG()
		self.fileCount = fileCount
		self.processed = 0
		self.pDialog.create(heading, message)

	def close(self):
		self.pDialog.close()

	def update(self, filename):
		self.processed += 1
		self.pDialog.update(int(self.processed / self.fileCount * 100), message=filename)

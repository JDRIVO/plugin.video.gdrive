import os
import time
import random
import threading
import traceback

import xbmc

from helpers import getCurrentTime, strToDatetime
from .syncer import Syncer
from .sync_cache_manager import SyncCacheManager
from ..filesystem.folder import Folder
from ..threadpool.threadpool import ThreadPool
from ..google_api.google_drive import GoogleDrive
from ..ui.dialogs import Dialog, SyncProgressionDialog
from ..filesystem.file_operations import FileOperations


class TaskManager:

	def __init__(self, settings, accountManager):
		self.settings = settings
		self.accountManager = accountManager
		self.accounts = self.accountManager.accounts
		self.cloudService = GoogleDrive()
		self.cache = SyncCacheManager()
		self.fileOperations = FileOperations(cloud_service=self.cloudService)
		self.syncer = Syncer(self.accountManager, self.cloudService, self.fileOperations, self.settings, self.cache)
		self.monitor = xbmc.Monitor()
		self.dialog = Dialog()
		self.taskLock = threading.Lock()
		self.idLock = threading.Lock()
		self.tasks = {}
		self.ids = []
		self.activeTasks = []

	def addTask(self, driveID, folders):
		self.activeTasks.append(driveID)
		self.accountManager.setAccounts()
		self.accounts = self.accountManager.accounts
		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.cloudService.refreshToken()
		syncRootPath = self.cache.getSyncRootPath()

		if not os.path.exists(syncRootPath):
			self.fileOperations.createDirs(syncRootPath)

		driveSettings = self.cache.getDrive(driveID)
		drivePath = os.path.join(syncRootPath, driveSettings["local_path"])
		folderTotal = len(folders)
		threadCount = self.settings.getSettingInt("thread_count", 1)

		if self.settings.getSetting("sync_progress_dialog"):
			progressDialog = SyncProgressionDialog(folderTotal)
			progressDialog.create()
		else:
			progressDialog = None

		with self.taskLock:

			with ThreadPool(threadCount) as pool:

				for folder in folders:
					folderID = folder["id"]
					folderName = folder["name"]
					dirPath = folder["path"]
					modifiedTime = folder["modifiedTime"]
					folderSettings = self.cache.getFolder({"folder_id": folderID})
					folder = Folder(folderID, folderID, folderID, driveID, folderName, dirPath, os.path.join(drivePath, dirPath), syncRootPath, folderSettings["folder_renaming"], modifiedTime)
					pool.submit(self.syncer.syncFolderAdditions, syncRootPath, drivePath, folder, folderSettings, progressDialog)

		if progressDialog:
			progressDialog.close()

		if not driveSettings["page_token"]:
			self.cache.updateDrive({"page_token": self.cloudService.getPageToken()}, driveID)

		self.dialog.notification(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30044))
		self.spawnTask(driveSettings, startUpRun=False)
		self.activeTasks.remove(driveID)

	def removeAllTasks(self):
		drives = self.cache.getDrives()
		[self.removeTask(drive["drive_id"]) for drive in drives]

	def removeTask(self, driveID):

		if driveID in self.tasks:
			del self.tasks[driveID]

			while driveID in self.activeTasks:
				time.sleep(0.1)

	def resetTask(self, driveID):
		self.removeTask(driveID)
		self.spawnTask(self.cache.getDrive(driveID), startUpRun=False)

	def run(self):
		drives = self.cache.getDrives()
		[self.spawnTask(driveSettings) for driveSettings in drives]

	def spawnTask(self, driveSettings, startUpRun=True):
		taskMode = driveSettings["task_mode"]
		startupSync = driveSettings["startup_sync"]
		driveID = driveSettings["drive_id"]

		if taskMode == "manual":

			if startUpRun and startupSync:
				self.sync(driveID)

			return

		taskFrequency = driveSettings["task_frequency"]
		taskID = self._createTaskID()
		self.tasks[driveID] = taskID

		if taskMode == "schedule":
			taskFrequency = strToDatetime(taskFrequency.lstrip())
			threading.Thread(target=self._startScheduledTask, args=(startupSync, taskFrequency, driveID, taskID, startUpRun)).start()
		else:
			taskFrequency = int(taskFrequency) * 60
			threading.Thread(target=self._startIntervalTask, args=(startupSync, taskFrequency, driveID, taskID, startUpRun)).start()

	def sync(self, driveID):

		if not self.cache.getFolder({"drive_id": driveID}):
			return

		self.activeTasks.append(driveID)
		synced = False

		try:

			with self.taskLock:
				synced = self.syncer.syncChanges(driveID)

		except Exception as e:
			xbmc.log(f"gdrive error: {e}: {''.join(traceback.format_tb(e.__traceback__))}", xbmc.LOGERROR)

		self.activeTasks.remove(driveID)
		return synced

	def syncAll(self):
		drives = self.cache.getDrives()
		return any([self.sync(drive["drive_id"]) for drive in drives])

	def _createTaskID(self):

		with self.idLock:
			id = random.random()

			while id in self.ids:
				id = random.random()

			self.ids.append(id)
			return id

	def _startIntervalTask(self, startupSync, taskFrequency, driveID, taskID, startUpRun=True):
		lastUpdate = time.time()

		while not self.monitor.abortRequested():

			if self.tasks.get(driveID) != taskID:
				self.ids.remove(taskID)
				return

			if not startupSync and startUpRun:
				startUpRun = False
				continue

			if time.time() - lastUpdate < taskFrequency and not startUpRun:

				if self.monitor.waitForAbort(1):
					break

				continue

			startUpRun = False
			self.sync(driveID)
			lastUpdate = time.time()

	def _startScheduledTask(self, startupSync, taskFrequency, driveID, taskID, startUpRun=True):

		while not self.monitor.abortRequested():

			if self.tasks.get(driveID) != taskID:
				self.ids.remove(taskID)
				return

			if not startupSync and startUpRun:
				startUpRun = False
				continue

			currentTime = getCurrentTime()

			if currentTime != taskFrequency and not startUpRun:

				if self.monitor.waitForAbort(1):
					break

				continue

			startUpRun = False
			self.sync(driveID)

import os
import time
import random
import threading
import traceback

import xbmc

from .syncer import Syncer
from .sync_cache import Cache
from ..filesystem.folder import Folder
from ..encryption.encryptor import Encryptor
from ..threadpool.threadpool import ThreadPool
from ..google_api.google_drive import GoogleDrive
from ..ui.dialogs import Dialog, SyncProgressionDialog
from ..filesystem.file_operations import FileOperations
from helpers import getCurrentTime, strToDatetime


class TaskManager:

	def __init__(self, settings, accountManager):
		self.settings = settings
		self.accountManager = accountManager
		self.accounts = self.accountManager.accounts
		self.cloudService = GoogleDrive()
		self.encryptor = Encryptor(settings=self.settings)
		self.cache = Cache()
		self.fileOperations = FileOperations(cloud_service=self.cloudService, encryption=self.encryptor)
		self.syncer = Syncer(self.accountManager, self.cloudService, self.encryptor, self.fileOperations, self.settings, self.cache)
		self.monitor = xbmc.Monitor()
		self.dialog = Dialog()
		self.taskLock = threading.Lock()
		self.idLock = threading.Lock()
		self.tasks = {}
		self.ids = []
		self.activeTasks = []

	def addTask(self, driveID, folders):
		self.activeTasks.append(driveID)
		self.encryptor.setup(settings=self.settings)
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
					folder = Folder(folderID, folderID, folderName, dirPath, os.path.join(drivePath, dirPath), modifiedTime)
					pool.submit(self.syncer.syncFolderAdditions, syncRootPath, drivePath, folder, folderSettings, progressDialog)

		if progressDialog:
			progressDialog.close()

		if not driveSettings["page_token"]:
			self.cache.updateDrive({"page_token": self.cloudService.getPageToken()}, driveID)

		if self.settings.getSetting("update_library"):
			xbmc.executebuiltin(f"UpdateLibrary(video,{syncRootPath})")

		self.dialog.notification(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30044))
		self._spawnTask(driveSettings, startUpRun=False)
		self.activeTasks.remove(driveID)

	def removeTask(self, driveID):

		if driveID in self.tasks:
			del self.tasks[driveID]
			time.sleep(2)

			while driveID in self.activeTasks:
				time.sleep(0.1)

	def resetTask(self, driveID):
		self.removeTask(driveID)
		self._spawnTask(self.cache.getDrive(driveID), startUpRun=False)

	def run(self):
		drives = self.cache.getDrives()

		if not drives:
			return

		for driveSettings in drives:
			self._spawnTask(driveSettings)

	def sync(self, driveID):
		self.activeTasks.append(driveID)

		try:

			with self.taskLock:
				self.syncer.syncChanges(driveID)

		except Exception as e:
			xbmc.log(f"gdrive error: {e}: {''.join(traceback.format_tb(e.__traceback__))}", xbmc.LOGERROR)

		self.activeTasks.remove(driveID)

	def syncAll(self):
		drives = self.cache.getDrives()

		if not drives:
			return

		for driveSettings in drives:
			self.sync(driveSettings["drive_id"])

	def _createTaskID(self):

		with self.idLock:
			id = random.random()

			while id in self.ids:
				id = random.random()

			self.ids.append(id)
			return id

	def _spawnTask(self, driveSettings, startUpRun=True):
		driveID = driveSettings["drive_id"]
		taskMode = driveSettings["task_mode"]
		taskFrequency = driveSettings["task_frequency"]
		startupSync = driveSettings["startup_sync"]
		taskID = self._createTaskID()
		self.tasks[driveID] = taskID

		if taskMode == "schedule":
			taskFrequency = strToDatetime(taskFrequency.lstrip())
			threading.Thread(target=self._startScheduledTask, args=(startupSync, taskFrequency, driveID, taskID, startUpRun)).start()
		else:
			taskFrequency = int(taskFrequency) * 60
			threading.Thread(target=self._startIntervalTask, args=(startupSync, taskFrequency, driveID, taskID, startUpRun)).start()

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

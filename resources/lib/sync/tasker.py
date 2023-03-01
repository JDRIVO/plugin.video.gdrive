import os
import time
import datetime
from threading import Thread

import xbmc
import xbmcgui

from .. import ui
from . import cache
from .. import sync
from .. import google_api
from .. import encryption
from .. import filesystem


class Tasker:

	def __init__(self, settings, accountManager):
		self.settings = settings
		self.accountManager = accountManager
		self.accounts = self.accountManager.accounts
		self.cloudService = google_api.drive.GoogleDrive()
		self.encrypter = encryption.encrypter.Encrypter(settings=self.settings)
		self.cache = cache.Cache()
		self.fileOperations = filesystem.operations.FileOperations(cloud_service=self.cloudService, encryption=self.encrypter)
		self.fileTree = filesystem.tree.FileTree(self.cloudService)
		self.fileProcessor = filesystem.processor.FileProcessor(self.cloudService, self.fileOperations, self.settings, self.cache)
		self.syncer = sync.syncer.Syncer(self.accountManager, self.cloudService, self.encrypter, self.fileOperations, self.fileProcessor, self.fileTree, self.settings, self.cache)
		self.monitor = xbmc.Monitor()
		self.dialog = xbmcgui.Dialog()
		self.tasks = {}
		self.taskIDs = []
		self.id = 0

	def run(self):
		drives = self.cache.getDrives()

		if not drives:
			return

		for driveSettings in drives:
			self.spawnTask(driveSettings)

	@staticmethod
	def strptime(dateString, format):
		return datetime.datetime(*(time.strptime(dateString, format)[0:6]))

	@staticmethod
	def floorDT(dt, interval):
		replace = (dt.minute // interval)*interval
		return dt.replace(minute = replace, second=0, microsecond=0)

	def removeTask(self, driveID):

		if driveID in self.tasks:
			del self.tasks[driveID]

	def spawnTask(self, driveSettings, startUpRun=True):
		driveID = driveSettings["drive_id"]
		taskMode = driveSettings["task_mode"]
		taskFrequency = driveSettings["task_frequency"]
		startupSync = driveSettings["startup_sync"]
		self.removeTask(driveID)
		self.id += 1
		id = self.id
		self.taskIDs.append(id)
		self.tasks[driveID] = id

		if taskMode == "schedule":
			taskFrequency = self.strptime(taskFrequency.lstrip(), "%H:%M").time()
			Thread(target=self.scheduledTask, args=(startupSync, taskFrequency, driveID, id, startUpRun)).start()
		else:
			taskFrequency = int(taskFrequency) * 60
			Thread(target=self.intervalTask, args=(startupSync, taskFrequency, driveID, id, startUpRun)).start()

	def intervalTask(self, startupSync, taskFrequency, driveID, taskID, startUpRun=True):
		lastUpdate = time.time()

		while True and not self.monitor.abortRequested():

			if taskID not in self.taskIDs:
				return

			if not startupSync and startUpRun:
				startUpRun = False
				continue

			currentTime = time.time()

			if currentTime - lastUpdate < taskFrequency and not startUpRun:

				if self.monitor.waitForAbort(1):
					# self.saveSyncSettings()
					break

				continue

			startUpRun = False
			self.syncer.syncChanges(driveID)
			lastUpdate = time.time()

	def scheduledTask(self, startupSync, taskFrequency, driveID, taskID, startUpRun=True):

		while True and not self.monitor.abortRequested():

			if taskID not in self.taskIDs:
				return

			if not startupSync and startUpRun:
				startUpRun = False
				continue

			currentTime = self.floorDT(datetime.datetime.now().time(), 1)

			if currentTime != taskFrequency and not startUpRun:

				if self.monitor.waitForAbort(1):
					# self.saveSyncSettings()
					break

				continue

			startUpRun = False
			self.syncer.syncChanges(driveID)

			if self.monitor.waitForAbort(60):
				# self.saveSyncSettings()
				break

	def createTask(self, driveID, folderID, folderName):
		self.encrypter.setup(settings=self.settings)
		self.accountManager.loadAccounts()
		self.accounts = self.accountManager.accounts
		syncRootPath = self.cache.select("global", "local_path")

		if syncRootPath:
			driveSettings = self.cache.getDrive(driveID)
		else:
			driveSettings = False
			syncRootPath = self.dialog.browse(0, "Select the folder that your files will be stored in", "files")

			if not syncRootPath:
				return

			syncRootPath = os.path.join(syncRootPath, "gDrive")
			self.cache.addGlobalData({"local_path": syncRootPath, "operating_system": os.name})

		if not driveSettings:
			modes = ["Sync at set inverval", "Sync at set time of day"]
			selection = self.dialog.select("Sync mode", modes)
			startupSyncPrompt = True
			pageToken = None

			if selection == -1:
				return

			if selection == 0:
				taskMode  = "interval"
				taskFrequency = self.dialog.numeric(0, "Enter the sync interval in minutes")

			else:
				taskMode = "schedule"
				taskFrequency = self.dialog.numeric(2, "Enter the time to sync files")

			if not taskFrequency:
				return

			alias = self.accounts[driveID]["alias"]
			drivePath = alias if alias else driveID

			driveSettings = {
				"drive_id": driveID,
				"local_path": drivePath,
				"page_token": pageToken,
				"last_update": time.time(),
				"task_mode": taskMode,
				"task_frequency": taskFrequency,
				"startup_sync": None,
			}
			self.cache.addDrive(driveSettings)
		else:
			driveSettings = self.cache.getDrive(driveID)
			taskMode = driveSettings["task_mode"]
			taskFrequency = driveSettings["task_frequency"]
			startupSync = driveSettings["startup_sync"]
			pageToken = driveSettings["page_token"]
			drivePath = driveSettings["local_path"]
			startupSyncPrompt = False

		syncOptions = ui.sync_settings.SyncOptions(startup_sync=startupSyncPrompt)
		syncOptions.doModal()

		if syncOptions.closed:
			del syncOptions
			return

		syncChoices = syncOptions.settings
		del syncOptions
		self.dialog.notification("gDrive", "Syncing files. A notification will appear when this task has completed.")

		if startupSyncPrompt:
			startupSync = syncChoices["startup_sync"]
			self.cache.updateDrive({"startup_sync": startupSync}, driveID)

		folderSettings = {
			"drive_id": driveID,
			"folder_id": folderID,
			"local_path": folderName,
			"file_renaming": False if not syncChoices["file_renaming"] else True,
			"folder_restructure": False if not syncChoices["folder_structure"] else True,
			"contains_encrypted": syncChoices["contains_encrypted"],
			"sync_artwork": syncChoices["sync_artwork"],
			"sync_nfo": syncChoices["sync_nfos"],
			"sync_subtitles": syncChoices["sync_subtitles"],
		}
		self.cache.addFolder(folderSettings)
		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.cloudService.refreshToken()
		self.syncer.syncFolderAdditions(syncRootPath, drivePath, folderName, folderSettings, folderID, folderID, folderID, driveID)

		if not pageToken:
			self.cache.updateDrive({"page_token": self.cloudService.getPageToken()}, driveID)

		xbmc.executebuiltin(f"UpdateLibrary(video,{syncRootPath})")
		xbmc.executebuiltin("Container.Refresh")
		self.dialog.notification("gDrive", "Sync Completed")
		self.spawnTask(driveSettings, startUpRun=False)

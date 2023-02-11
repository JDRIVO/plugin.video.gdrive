import os
import time
import datetime
from threading import Thread

import xbmc
import xbmcgui

from .. import ui
from .. import sync
from .. import google_api
from .. import encryption
from .. import filesystem


class Tasker:

	def __init__(self, settings, accountManager):
		self.settings = settings
		self.accountManager = accountManager
		self.accounts = self.accountManager.accounts
		self.cloudService = google_api.drive.GoogleDrive(self.accountManager)
		self.encrypter = encryption.encrypter.Encrypter(settings=self.settings)
		self.fileOperations = filesystem.operations.FileOperations(self.cloudService, self.encrypter)
		self.fileTree = filesystem.tree.FileTree(self.cloudService, self.encrypter)
		self.fileProcessor = filesystem.processor.FileProcessor(self.cloudService, self.fileOperations, self.settings)
		self.syncer = sync.syncer.Syncer(self.accountManager, self.cloudService, self.encrypter, self.fileOperations, self.fileProcessor, self.fileTree, self.settings)
		self.monitor = xbmc.Monitor()
		self.dialog = xbmcgui.Dialog()
		self.tasks = {}
		self.taskIDs = []
		self.id = 0

	def run(self):
		syncSettings = self.settings.getSyncSettings()

		if not syncSettings:
			return

		for driveID, driveSettings in syncSettings["drives"].items():
			taskDetails = driveSettings["task_details"]
			self.spawnTask(taskDetails, driveID)

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

	def spawnTask(self, taskDetails, driveID, startUpRun=True):
		mode = taskDetails["mode"]
		syncTime = taskDetails["frequency"]
		startupSync = taskDetails["startup_sync"]
		self.removeTask(driveID)

		self.id += 1
		id = self.id
		self.taskIDs.append(id)
		self.tasks[driveID] = id

		if mode == "schedule":
			syncTime = self.strptime(syncTime.lstrip(), "%H:%M").time()
			Thread(target=self.scheduledTask, args=(startupSync, syncTime, driveID, id, startUpRun)).start()
		else:
			syncTime = int(syncTime) * 60
			Thread(target=self.intervalTask, args=(startupSync, syncTime, driveID, id, startUpRun)).start()

	def intervalTask(self, startupSync, syncTime, driveID, taskID, startUpRun=True):
		lastUpdate = time.time()

		while True and not self.monitor.abortRequested():

			if taskID not in self.taskIDs:
				return

			if not startupSync and startUpRun:
				startUpRun = False
				continue

			currentTime = time.time()

			if currentTime - lastUpdate < syncTime and not startUpRun:

				if self.monitor.waitForAbort(1):
					# self.saveSyncSettings()
					break

				continue

			startUpRun = False
			self.syncer.syncChanges(driveID, self.settings.getSyncSettings())
			lastUpdate = time.time()

	def scheduledTask(self, startupSync, syncTime, driveID, taskID, startUpRun=True):

		while True and not self.monitor.abortRequested():

			if taskID not in self.taskIDs:
				return

			if not startupSync and startUpRun:
				startUpRun = False
				continue

			currentTime = self.floorDT(datetime.datetime.now().time(), 1)

			if currentTime != syncTime and not startUpRun:

				if self.monitor.waitForAbort(1):
					# self.saveSyncSettings()
					break

				continue

			startUpRun = False
			self.syncer.syncChanges(driveID, self.settings.getSyncSettings())

			if self.monitor.waitForAbort(60):
				# self.saveSyncSettings()
				break

	def createTask(self, driveID, folderID, folderName):
		self.encrypter.setup(settings=self.settings)
		syncSettings = self.settings.getSyncSettings()

		if syncSettings:
			gdriveRoot = syncSettings["local_path"]
			driveSettings = syncSettings["drives"].get(driveID)
		else:
			driveSettings = {}
			gdriveRoot = self.dialog.browse(0, "Select the folder that your files will be stored in", "files")

			if not gdriveRoot:
				return

			gdriveRoot = os.path.join(gdriveRoot, "gDrive")
			syncSettings["local_path"] = gdriveRoot
			syncSettings["drives"] = {}

		if not driveSettings:
			modes = ["Sync at set inverval", "Sync at set time of day"]
			selection = self.dialog.select("Sync mode", modes)
			taskDetails = {}
			startupSync = True

			if selection == -1:
				return

			if selection == 0:
				taskDetails["mode"] = "interval"
				frequency = self.dialog.numeric(0, "Enter the sync interval in minutes")

			else:
				taskDetails["mode"] = "schedule"
				frequency = self.dialog.numeric(2, "Enter the time to sync files")

			if not frequency:
				return

			taskDetails["frequency"] = frequency
			syncSettings["drives"][driveID] = {
				"alias": None,
				"page_token": None,
				"folders": {},
				"last_update": time.time(),
				"files": {},
				"directories": {},
				"local_path": os.path.join(gdriveRoot, driveID),
				"task_details": taskDetails,
			}
			driveSettings = syncSettings["drives"][driveID]

		else:
			taskDetails = driveSettings["task_details"]
			startupSync = False

		syncOptions = ui.sync_settings.SyncOptions(startup_sync=startupSync)
		syncOptions.doModal()
		syncChoices = syncOptions.settings

		if syncOptions.closed:
			return

		del syncOptions
		self.dialog.notification("gDrive", "Generating files please wait. A notification will appear when this task has completed.")

		if startupSync:
			taskDetails["startup_sync"] = syncChoices["startup_sync"]

		if not syncChoices["folder_structure"]:
			folderStructure = "original"
		else:
			folderStructure = "kodi_friendly"

		if not syncChoices["file_renaming"]:
			fileRenaming = "original"
		else:
			fileRenaming = "kodi_friendly"

		driveSettings["folders"][folderID] = {
			"folder_structure": folderStructure,
			"file_renaming": fileRenaming,
			"sync_artwork": syncChoices["sync_artwork"],
			"sync_nfo": syncChoices["sync_nfos"],
			"sync_subtitles": syncChoices["sync_subtitles"],
			"local_path": os.path.join(gdriveRoot, driveID, folderName),
			"contains_encrypted": syncChoices["contains_encrypted"],
		}

		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.cloudService.refreshToken()

		syncRoot = syncSettings["local_path"]
		folderSettings = driveSettings["folders"][folderID]
		dirPath = folderSettings["local_path"]

		cachedDirectories = driveSettings["directories"]
		cachedFiles = driveSettings["files"]
		self.syncer.syncFolderAdditions(syncRoot, dirPath, folderSettings, cachedDirectories, cachedFiles, folderID, folderID, folderID, driveID)

		if not driveSettings.get("page_token"):
			driveSettings["page_token"] = self.cloudService.getPageToken()

		self.settings.saveSyncSettings(syncSettings)
		xbmc.executebuiltin("UpdateLibrary(video,{})".format(syncRoot))
		xbmc.executebuiltin("Container.Refresh")
		self.dialog.notification("gDrive", "Sync Completed")
		self.spawnTask(taskDetails, driveID, startUpRun=False)

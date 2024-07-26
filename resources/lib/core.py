import os
import sys
import glob
import json
import time
import urllib
import datetime

import xbmc
import xbmcgui
import xbmcplugin

import constants
from . import ui
from . import sync
from . import accounts
from . import filesystem
from . import google_api
from . import threadpool


class Core:

	def __init__(self):
		self.pluginURL = sys.argv[0]
		self.pluginHandle = int(sys.argv[1])
		self.settings = constants.settings
		self.mode = self.settings.getParameter("mode", "main")
		self.cache = sync.cache.Cache()
		self.accountManager = accounts.manager.AccountManager(self.settings)
		self.accounts = self.accountManager.accounts
		self.cloudService = google_api.drive.GoogleDrive()
		self.dialog = xbmcgui.Dialog()
		self.succeeded = True
		self.cacheToDisk = True

	def run(self, dbID, dbType, filePath):

		if self.pluginHandle < 0 and "search_folder" in sys.argv[2]:
			xbmc.executebuiltin(f"Container.Update({sys.argv[0] + sys.argv[2]})")
			return

		modes = {
			"main": self.createMainMenu,
			"register_account": self.registerAccount,
			"add_service_account": self.addServiceAccount,
			"validate_accounts": self.validateAccounts,
			"delete_accounts": self.accountDeletion,
			"list_drive": self.createDriveMenu,
			"list_drives": self.createDrivesMenu,
			"list_accounts": self.listAccounts,
			"list_folders": self.addFolders,
			"list_synced_folders": self.listSyncedFolders,
			"video": self.playVideo,
			"get_sync_settings": self.getSyncSettings,
			"sync_folder": self.syncFolder,
			"sync_all_folders": self.syncAllFolders,
			"sync_multiple_folders": self.syncMultipleFolders,
			"resolution_priority": self.resolutionPriority,
			"force_sync": self.forceSync,
			"force_sync_all": self.forceSyncAll,
			"accounts_cm": self.accountsContextMenu,
			"list_shared_drives": self.listSharedDrives,
			"search_drive": self.searchDrive,
			"search_folder": self.searchFolder,
			"import_accounts": self.importAccounts,
			"export_accounts": self.exportAccounts,
			"set_playback_account": self.setPlaybackAccount,
			"set_alias": self.setAlias,
			"delete_drive": self.deleteDrive,
			"set_tmdb_language": self.setTMDBlanguage,
			"set_tmdb_region": self.setTMDBregion,
		}

		if self.mode == "video":
			modes[self.mode](dbID, dbType, filePath)
		else:
			modes[self.mode]()

		xbmcplugin.endOfDirectory(self.pluginHandle, succeeded=self.succeeded, cacheToDisc=self.cacheToDisk)

	def accountsContextMenu(self):
		options = [
			self.settings.getLocalizedString(30002),
			self.settings.getLocalizedString(30023),
			self.settings.getLocalizedString(30159),
		]
		driveID = self.settings.getParameter("drive_id")
		accountName = self.settings.getParameter("account_name")
		accountIndex = int(self.settings.getParameter("account_index"))
		selection = self.dialog.contextmenu(options)
		accounts = self.accountManager.getAccounts(driveID)
		account = accounts[accountIndex]

		if selection == 0:
			newAccountName = self.dialog.input(self.settings.getLocalizedString(30025))

			if not newAccountName:
				return

			self.accountManager.renameAccount(driveID, accountIndex, newAccountName)

		elif selection == 1:
			self.cloudService.setAccount(account)
			tokenRefresh = self.cloudService.refreshToken()

			if tokenRefresh == "failed":
				selection = self.dialog.yesno(
					self.settings.getLocalizedString(30000),
					f"{accountName} {self.settings.getLocalizedString(30019)}",
				)

				if not selection:
					return

				self.accountManager.deleteAccount(driveID, account)

			else:
				self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30020))
				return

		elif selection == 2:
			selection = self.dialog.yesno(
				self.settings.getLocalizedString(30000),
				f"{self.settings.getLocalizedString(30121)} {accountName}?",
			)

			if not selection:
				return

			self.accountManager.deleteAccount(driveID, account)

		else:
			return

		xbmc.executebuiltin("Container.Refresh")

	def addMenu(self, url, title, cm=False, folder=True):
		listItem = xbmcgui.ListItem(title)

		if cm:
			listItem.addContextMenuItems(cm, True)

		xbmcplugin.addDirectoryItem(self.pluginHandle, url, listItem, isFolder=folder)

	def createMainMenu(self):
		syncRootPath = self.cache.getSyncRootPath()

		if syncRootPath:
			self.addMenu(
				syncRootPath,
				f"[COLOR yellow][B]{self.settings.getLocalizedString(30008)}[/B][/COLOR]",
			)

		contextMenu = [
			(
				self.settings.getLocalizedString(30010),
				f"RunPlugin({self.pluginURL}?mode=force_sync_all)",
			),
		]
		self.addMenu(
			f"{self.pluginURL}?mode=list_drives",
			f"[COLOR yellow][B]{self.settings.getLocalizedString(30085)}[/B][/COLOR]",
			cm=contextMenu,
		)
		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_FILE)
		self.cacheToDisk = False

	def createDrivesMenu(self):
		self.addMenu(
			f"{self.pluginURL}?mode=register_account",
			f"[B][COLOR yellow]{self.settings.getLocalizedString(30207)}[/COLOR][/B]",
			folder=False,
		)
		self.addMenu(
			f"{self.pluginURL}?mode=import_accounts",
			f"[B][COLOR yellow]{self.settings.getLocalizedString(30087)}[/COLOR][/B]",
			folder=False,
		)
		self.addMenu(
			f"{self.pluginURL}?mode=export_accounts",
			f"[COLOR yellow][B]{self.settings.getLocalizedString(30088)}[/B][/COLOR]",
			folder=False,
		)

		for driveID, accountData in self.accounts.items():
			alias = accountData["alias"]

			if alias:
				displayName = alias
			else:
				displayName = driveID

			contextMenu = [
				(
					self.settings.getLocalizedString(30800),
					f"RunPlugin({self.pluginURL}?mode=force_sync&drive_id={driveID})",
				),
				(
					self.settings.getLocalizedString(30002),
					f"RunPlugin({self.pluginURL}?mode=set_alias&drive_id={driveID})",
				),
				(
					self.settings.getLocalizedString(30159),
					f"RunPlugin({self.pluginURL}?mode=delete_drive&drive_id={driveID})",
				)
			]
			self.addMenu(
				f"{self.pluginURL}?mode=list_drive&drive_id={driveID}",
				displayName,
				cm=contextMenu,
			)

		xbmcplugin.setContent(self.pluginHandle, "files")
		# xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_FILE)
		# xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)

	def createDriveMenu(self):
		driveID = self.settings.getParameter("drive_id")
		account = self.accountManager.getAccount(driveID)

		if not account:
			return

		self.cloudService.setAccount(account)
		self.refreshAccess(account.expiry)
		driveSettings = self.cache.getDrive(driveID)

		if driveSettings:
			self.addMenu(
				f"{self.pluginURL}?mode=list_synced_folders&drive_id={driveID}",
				f"[COLOR yellow][B]{self.settings.getLocalizedString(30011)}[/B][/COLOR]",
			)

		self.addMenu(
			f"{self.pluginURL}?mode=list_accounts&drive_id={driveID}",
			f"[COLOR yellow][B]{self.settings.getLocalizedString(30032)}[/B][/COLOR]",
		)
		self.addMenu(
			f"{self.pluginURL}?mode=list_folders&drive_id={driveID}",
			self.settings.getLocalizedString(30038),
		)
		self.addMenu(
			f"{self.pluginURL}?mode=list_folders&drive_id={driveID}&shared_with_me=true",
			self.settings.getLocalizedString(30039),
		)
		self.addMenu(
			f"{self.pluginURL}?mode=list_shared_drives&drive_id={driveID}",
			self.settings.getLocalizedString(30040),
		)
		self.addMenu(
			f"{self.pluginURL}?mode=search_drive&drive_id={driveID}",
			self.settings.getLocalizedString(30041),
		)
		self.addMenu(
			f"{self.pluginURL}?mode=list_folders&drive_id={driveID}&starred=true",
			self.settings.getLocalizedString(30042),
		)
		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_LABEL)

	def listAccounts(self):
		driveID = self.settings.getParameter("drive_id")
		account = self.accountManager.getAccount(driveID)

		if not account:
			return

		self.cloudService.setAccount(account)
		self.refreshAccess(account.expiry)

		self.addMenu(
			f"{self.pluginURL}?mode=add_service_account&drive_id={driveID}",
			f"[B][COLOR yellow]{self.settings.getLocalizedString(30214)}[/COLOR][/B]",
			folder=False,
		)
		self.addMenu(
			f"{self.pluginURL}?mode=validate_accounts&drive_id={driveID}",
			f"[B][COLOR yellow]{self.settings.getLocalizedString(30021)}[/COLOR][/B]",
			folder=False,
		)
		self.addMenu(
			f"{self.pluginURL}?mode=delete_accounts&drive_id={driveID}",
			f"[B][COLOR yellow]{self.settings.getLocalizedString(30022)}[/COLOR][/B]",
			folder=False,
		)

		for index, account in enumerate(self.accountManager.getAccounts(driveID)):
			accountName = account.name
			self.addMenu(
				f"{self.pluginURL}?mode=accounts_cm&account_name={accountName}&account_index={index}&drive_id={driveID}",
				f"[COLOR lime][B]{accountName}[/B][/COLOR]",
				folder=False,
			)

		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_LABEL)

	def searchFolder(self):
		searchQuery = xbmcgui.Dialog().input(self.settings.getLocalizedString(30043))

		if not searchQuery:
			self.succeeded = False
			return

		searchQuery = searchQuery.lower()
		driveID = self.settings.getParameter("drive_id")
		sharedDriveID = self.settings.getParameter("shared_drive_id")
		folderID = self.settings.getParameter("folder_id")
		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.refreshAccess(account.expiry)

		if not folderID:

			if sharedDriveID:
				folderID = sharedDriveID
			else:
				folderID = driveID

		folders = []
		folderIDs = [folderID]
		threadCount = self.settings.getSettingInt("thread_count", 1)
		self.getSpecificFolders(searchQuery, folders, folderIDs, threadCount)
		self.listFolders(driveID, folders)

	def searchDrive(self):
		searchQuery = xbmcgui.Dialog().input(self.settings.getLocalizedString(30043))

		if not searchQuery:
			self.succeeded = False
			return

		driveID = self.settings.getParameter("drive_id")
		folders = self.getFolders(driveID, driveID, search=searchQuery)
		self.listFolders(driveID, folders)

	def listSharedDrives(self):
		driveID = self.settings.getParameter("drive_id")
		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.refreshAccess(account.expiry)
		sharedDrives = self.cloudService.getDrives()

		if sharedDrives:

			for sharedDrive in sharedDrives:
				sharedDriveID = sharedDrive["id"]
				sharedDriveName = sharedDrive["name"]
				self.addMenu(
					f"{self.pluginURL}?mode=list_folders&drive_id={driveID}&shared_drive_id={sharedDriveID}",
					f"[B]{sharedDriveName}[/B]",
				)

	def getSyncSettings(self):
		driveID = self.settings.getParameter("drive_id")
		folderID = self.settings.getParameter("folder_id")
		folderName = self.settings.getParameter("folder_name")
		mode = self.settings.getParameter("sync_mode")
		self.succeeded=False

		syncSettings = ui.sync_settings.SyncSettings(drive_id=driveID, folder_id=folderID, accounts=self.accounts, folder_name=folderName, mode=mode)
		syncSettings.doModal()
		del syncSettings

	def addFolders(self):
		driveID = self.settings.getParameter("drive_id")
		folderID = self.settings.getParameter("folder_id")
		sharedDriveID = self.settings.getParameter("shared_drive_id")

		if not folderID:

			if sharedDriveID:
				folderID = sharedDriveID
			else:
				folderID = driveID

		folders = self.getFolders(driveID, folderID)
		self.listFolders(driveID, folders, folderID)

	def getFolders(self, driveID, folderID, search=False):
		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.refreshAccess(account.expiry)
		sharedWithMe = self.settings.getParameter("shared_with_me")
		starred = self.settings.getParameter("starred")
		return self.cloudService.listDirectory(folderID=folderID, sharedWithMe=sharedWithMe, foldersOnly=True, starred=starred, search=search)

	def getSpecificFolders(self, searchQuery, folders, folderIDs, threadCount):

		def getFolders(query):
			folders_ = self.cloudService.listDirectory(customQuery=query)
			filterFolders(folders_, folders, searchQuery, folderIDs)

		def filterFolders(folders_, folders, searchQuery, folderIDs):

			for folder in folders_:
				folderName = folder["name"]
				folderID = folder["id"]
				parentFolderID = folder["parents"][0]
				folderIDs.append(folderID)

				if searchQuery in [str.lower() for str in folderName.split()]:
					folders.append({"name": folderName, "id": folderID, "parent_id": parentFolderID})

		maxIDs = 100
		queries = []

		while folderIDs:
			ids = folderIDs[:maxIDs]
			queries.append("mimeType='application/vnd.google-apps.folder' and not trashed and (" + " or ".join(f"'{id}' in parents" for id in ids) + ")")
			folderIDs = folderIDs[maxIDs:]

		with threadpool.threadpool.ThreadPool(threadCount) as pool:
			pool.map(getFolders, [(query,) for query in queries])

		if folderIDs:
			self.getSpecificFolders(searchQuery, folders, folderIDs, threadCount)

	def listFolders(self, driveID, folders, parentFolderID=None):
		sharedWithMe = self.settings.getParameter("shared_with_me")

		for folder in folders:
			folderID = folder["id"]
			folderName = folder["name"]
			folderSettings = self.cache.getFolder({"folder_id": folderID})

			if folderSettings:
				contextMenu = [
					(
						self.settings.getLocalizedString(30005),
						f"RunPlugin({self.pluginURL}?mode=get_sync_settings&sync_mode=folder&drive_id={driveID}&folder_id={folderID}&folder_name={folderName})",
					),
				]
				folderName = f"[COLOR lime][B]{folderName}[/B][/COLOR]"
			else:
				directory = self.cache.getDirectory({"folder_id": folderID})

				if directory:
					folderName = f"[COLOR springgreen][B]{folderName}[/B][/COLOR]"
					contextMenu = False
				else:
					contextMenu = [
						(
							self.settings.getLocalizedString(30013),
							f"RunPlugin({self.pluginURL}?mode=sync_folder&sync_mode=new&drive_id={driveID}&folder_id={folderID}&folder_name={folderName})",
						),
						(
							self.settings.getLocalizedString(30090),
							f"RunPlugin({self.pluginURL}?mode=sync_multiple_folders&sync_mode=new&drive_id={driveID}&parent_id={parentFolderID}&shared_with_me={sharedWithMe})",
						),
						(
							self.settings.getLocalizedString(30010),
							f"RunPlugin({self.pluginURL}?mode=sync_all_folders&sync_mode=new&drive_id={driveID}&parent_id={parentFolderID}&shared_with_me={sharedWithMe})",
						),
						(
							self.settings.getLocalizedString(30091),
							f"RunPlugin({self.pluginURL}?mode=search_folder&drive_id={driveID}&folder_id={folderID})",
						),
					]

					if self.mode in ("search_folder", "search_drive"):
						contextMenu = contextMenu[:1]

			self.addMenu(
				f"{self.pluginURL}?mode=list_folders&drive_id={driveID}&folder_id={folderID}",
				folderName,
				cm=contextMenu,
			)

		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_LABEL)

	def listSyncedFolders(self):
		driveID = self.settings.getParameter("drive_id")
		folders = self.cache.getFolders({"drive_id": driveID})
		self.addMenu(
			f"{self.pluginURL}?mode=get_sync_settings&drive_id={driveID}&sync_mode=drive",
			f"[B][COLOR yellow]{self.settings.getLocalizedString(30017)}[/COLOR][/B]",
			folder=False,
		)

		for folder in folders:
			folderName = folder["local_path"]
			folderID = folder["folder_id"]
			self.addMenu(
				f"{self.pluginURL}?mode=get_sync_settings&drive_id={driveID}&folder_id={folderID}&sync_mode=folder",
				f"[COLOR lime][B]{folderName}[/B][/COLOR]",
				folder=True,
			)

		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_FILE)

	def refreshAccess(self, expiry):
		timeNow = datetime.datetime.now()

		if timeNow >= expiry:
			self.cloudService.refreshToken()
			self.accountManager.saveAccounts()

	def forceSync(self):
		driveID = self.settings.getParameter("drive_id")
		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/force_sync"
		data = f"drive_id={driveID}"
		req = urllib.request.Request(url, data.encode("utf-8"))
		response = urllib.request.urlopen(req)
		response.close()

	def forceSyncAll(self):
		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/force_sync_all"
		req = urllib.request.Request(url)
		response = urllib.request.urlopen(req)
		response.close()

	def syncFolder(self):
		driveID = self.settings.getParameter("drive_id")
		folderID = self.settings.getParameter("folder_id")
		folderName = self.settings.getParameter("folder_name")
		folders = [{"id": folderID, "name": folderName}]
		mode = self.settings.getParameter("sync_mode")
		self.succeeded = False
		syncSettings = ui.sync_settings.SyncSettings(drive_id=driveID, accounts=self.accounts, folders=folders, mode=mode)
		syncSettings.doModal()
		del syncSettings

	def syncAllFolders(self):
		driveID = self.settings.getParameter("drive_id")
		parentFolderID = self.settings.getParameter("parent_id")
		mode = self.settings.getParameter("sync_mode")
		self.succeeded = False
		folders = self.getFolders(driveID, parentFolderID)
		syncSettings = ui.sync_settings.SyncSettings(drive_id=driveID, accounts=self.accounts, folders=folders, mode=mode)
		syncSettings.doModal()
		del syncSettings

	def syncMultipleFolders(self):
		driveID = self.settings.getParameter("drive_id")
		parentFolderID = self.settings.getParameter("parent_id")
		mode = self.settings.getParameter("sync_mode")
		self.succeeded = False
		folders = self.getFolders(driveID, parentFolderID)
		folderNames = [folder["name"] for folder in folders]
		chosenFolders = self.dialog.multiselect(self.settings.getLocalizedString(30086), folderNames)

		if not chosenFolders:
			return

		folders = [folders[index] for index in chosenFolders]
		syncSettings = ui.sync_settings.SyncSettings(drive_id=driveID, accounts=self.accounts, folders=folders, mode=mode)
		syncSettings.doModal()
		del syncSettings

	def registerAccount(self):
		self.dialog.ok(
			self.settings.getLocalizedString(30000),
			"{} [B][COLOR blue]http://localhost:{}/register[/COLOR][/B] {}\n\n{} [COLOR chartreuse]{}[/COLOR] {} [COLOR chartreuse]{}[/COLOR] {} [COLOR chartreuse]{}[/COLOR] [B][COLOR blue]http://localhost:{}/status[/COLOR][/B]".format(
				self.settings.getLocalizedString(30210),
				self.settings.getSetting("server_port"),
				self.settings.getLocalizedString(30218),
				self.settings.getLocalizedString(30222),
				self.settings.getLocalizedString(30223),
				self.settings.getLocalizedString(30224),
				self.settings.getLocalizedString(30225),
				self.settings.getLocalizedString(30226),
				self.settings.getLocalizedString(30227),
				self.settings.getSetting("server_port"),
			)
		)

	def addServiceAccount(self):
		accountName = self.dialog.input(self.settings.getLocalizedString(30025))

		if not accountName:
			return

		keyFilePath = self.dialog.browse(1, self.settings.getLocalizedString(30026), "files", mask=".json")

		if not keyFilePath:
			return

		with open(keyFilePath, "r") as key:
			keyFile = json.loads(key.read())

		error = []

		try:
			email = keyFile["client_email"]
		except Exception:
			error.append("email")

		try:
			key = keyFile["private_key"]
		except Exception:
			error.append("key")

		if error:

			if len(error) == 2:
				self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30028))
			elif "email" in error:
				self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30029))
			elif "key" in error:
				self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30030))

			return

		account = accounts.account.Account()
		account.name = accountName
		account.email = email
		account.key = key
		self.cloudService.setAccount(account)
		tokenRefresh = self.cloudService.refreshToken()

		if tokenRefresh == "failed":
			return

		driveID = self.settings.getParameter("drive_id")
		self.accountManager.addAccount(account, driveID)
		xbmc.executebuiltin("Container.Refresh")

	def validateAccounts(self):
		driveID = self.settings.getParameter("drive_id")
		accounts = self.accountManager.getAccounts(driveID)
		accountAmount = len(accounts)
		pDialog = xbmcgui.DialogProgress()

		pDialog.create(self.settings.getLocalizedString(30306))
		deletion = False
		count = 1

		for account in list(accounts):
			accountName = account.name

			if pDialog.iscanceled():
				return

			self.cloudService.setAccount(account)
			tokenRefresh = self.cloudService.refreshToken()
			pDialog.update(int(round(count / accountAmount * 100)), accountName)
			count += 1

			if tokenRefresh == "failed":
				selection = self.dialog.yesno(
					self.settings.getLocalizedString(30000),
					f"{accountName} {self.settings.getLocalizedString(30019)}",
				)

				if not selection:
					continue

				accounts.remove(account)
				deletion = True

		pDialog.close()
		self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30020))

		if deletion:
			xbmc.executebuiltin("Container.Refresh")

	def accountDeletion(self):
		driveID = self.settings.getParameter("drive_id")
		accounts = self.accountManager.getAccounts(driveID)
		accountNames = self.accountManager.getAccountNames(accounts)
		selection = self.dialog.multiselect(self.settings.getLocalizedString(30158), accountNames)

		if not selection:
			return

		self.accountManager.deleteAccounts(selection, accounts, driveID)
		self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30161))
		xbmc.executebuiltin("Container.Refresh")

	def resolutionPriority(self):
		resolutions = self.settings.getSetting("resolution_priority").split(", ")
		resolutionOrder = ui.resolution_order.ResolutionOrder(resolutions=resolutions)

		resolutionOrder.doModal()
		newOrder = resolutionOrder.priorityList
		del resolutionOrder

		if newOrder:
			self.settings.setSetting("resolution_priority", ", ".join(newOrder))

	def importAccounts(self):
		filePath = self.dialog.browse(1, self.settings.getLocalizedString(30033), "files", mask=".pkl")

		if not filePath:
			return

		imported = self.accountManager.mergeAccounts(filePath)

		if imported == "failed":
			self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30037))
		else:
			self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30036))
			xbmc.executebuiltin("Container.Refresh")

	def exportAccounts(self):
		filePath = self.dialog.browse(0, self.settings.getLocalizedString(30034), "")

		if not filePath:
			return

		self.accountManager.exportAccounts(filePath)
		self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30035))

	def setPlaybackAccount(self):
		accounts = self.accountManager.getDrives()
		displayNames = [account[1] for account in accounts]
		selection = self.dialog.select(self.settings.getLocalizedString(30014), displayNames)

		if selection == -1:
			return

		self.settings.setSetting("playback_account", accounts[selection][0])
		self.settings.setSetting("account_override", accounts[selection][1])

	def setAlias(self):
		driveID = self.settings.getParameter("drive_id")
		alias = self.dialog.input(self.settings.getLocalizedString(30004))

		if not alias:
			return

		alias = filesystem.helpers.removeProhibitedFSchars(alias)

		if alias in self.accountManager.aliases:
			self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30015))
			return

		xbmc.executebuiltin("ActivateWindow(busydialognocancel)")
		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/set_alias"
		data = f"drive_id={driveID}&alias={alias}"
		req = urllib.request.Request(url, data.encode("utf-8"))
		response = urllib.request.urlopen(req)
		response.close()

	def deleteDrive(self):

		confirmation = self.dialog.yesno(
			self.settings.getLocalizedString(30000),
			self.settings.getLocalizedString(30016),
		)

		if not confirmation:
			return

		xbmc.executebuiltin("ActivateWindow(busydialognocancel)")
		driveID = self.settings.getParameter("drive_id")
		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/delete_drive"
		data = f"drive_id={driveID}"
		req = urllib.request.Request(url, data.encode("utf-8"))
		response = urllib.request.urlopen(req)
		response.close()

	def setTMDBlanguage(self):
		selection = self.dialog.select(self.settings.getLocalizedString(30810), filesystem.helpers.TMDB_LANGUAGES)

		if selection == -1:
			return

		self.settings.setSetting("tmdb_language", filesystem.helpers.TMDB_LANGUAGES[selection])

	def setTMDBregion(self):
		selection = self.dialog.select(self.settings.getLocalizedString(30811), filesystem.helpers.TMDB_REGIONS)

		if selection == -1:
			return

		self.settings.setSetting("tmdb_region", filesystem.helpers.TMDB_REGIONS[selection])

	def playVideo(self, dbID, dbType, filePath):

		if (not dbID or not dbType) and not filePath:
			timeEnd = time.time() + 1

			while time.time() < timeEnd and (not dbID or not dbType):
				xbmc.executebuiltin("Dialog.Close(busydialog)")
				dbID = xbmc.getInfoLabel("ListItem.DBID")
				dbType = xbmc.getInfoLabel("ListItem.DBTYPE")
				filePath = xbmc.getInfoLabel("ListItem.FileNameAndPath")

		encrypted = self.settings.getParameter("encrypted")
		fileID = self.settings.getParameter("file_id")
		driveURL = self.cloudService.getDownloadURL(fileID)

		if self.settings.getSetting("account_selection") == "Manually selected":
			driveID = self.settings.getSetting("playback_account")
		else:
			driveID = self.settings.getParameter("drive_id")
			account = self.accountManager.getAccount(driveID)

		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.refreshAccess(account.expiry)
		transcoded = False

		if encrypted:

			if not self.settings.getSetting("crypto_password") or not self.settings.getSetting("crypto_salt"):
				self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30208))
				return

		else:
			resolutionPrompt = self.settings.getSetting("resolution_prompt")
			resolutionPriority = self.settings.getSetting("resolution_priority").split(", ")

			if resolutionPrompt:
				streams = self.cloudService.getStreams(fileID)

				if streams and len(streams) > 1:
					resolutionSelector = ui.resolution_selector.ResolutionSelector(resolutions=streams)
					resolutionSelector.doModal()

					if resolutionSelector.closed:
						del resolutionSelector
						return

					selection = resolutionSelector.resolution
					del resolutionSelector

					if selection != "Original":
						driveURL = streams[selection]
						transcoded = selection

			elif resolutionPriority[0] != "Original":
				stream = self.cloudService.getStreams(fileID, resolutionPriority)

				if stream:
					transcoded, driveURL = stream

		self.accountManager.saveAccounts()
		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/play_url"
		data = f"encrypted={encrypted}&url={driveURL}&drive_id={driveID}&file_id={fileID}&transcoded={transcoded}"
		req = urllib.request.Request(url, data.encode("utf-8"))

		try:
			response = urllib.request.urlopen(req)
			response.close()
		except urllib.error.URLError as e:
			xbmc.log("gdrive error: " + str(e))
			return

		item = xbmcgui.ListItem(path=f"http://localhost:{serverPort}/play")

		if self.settings.getSetting("subtitles_format") == "Subtitles are named the same as STRM":
			subtitles = glob.glob(glob.escape(filePath.rstrip(".strm")) + "*[!gom]")
			item.setSubtitles(subtitles)
		else:
			subtitles = glob.glob(glob.escape(os.path.dirname(filePath) + os.sep) + "*[!gom]")
			item.setSubtitles(subtitles)

		if dbID:
			data = f"db_id={dbID}&db_type={dbType}"
		else:
			data = "db_id=False&db_type=False"

		xbmcplugin.setResolvedUrl(self.pluginHandle, True, item)
		url = f"http://localhost:{serverPort}/start_player"
		req = urllib.request.Request(url, data.encode("utf-8"))
		response = urllib.request.urlopen(req)
		response.close()

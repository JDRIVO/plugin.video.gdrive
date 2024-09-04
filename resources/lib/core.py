import os
import sys
import glob
import json
import time
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
from .network import requester


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
		self.dialog = ui.dialogs.Dialog()
		self.succeeded = True
		self.cacheToDisk = True

	def run(self, dbID, dbType, filePath):

		if self.pluginHandle < 0 and self.mode == "search_folder":
			xbmc.executebuiltin(f"Container.Update({self.pluginURL + sys.argv[2]})")
			return

		modes = {
			"accounts_cm": self.showAccountsContextMenu,
			"add_service_account": self.addServiceAccount,
			"delete_accounts": self.accountDeletion,
			"delete_drive": self.deleteDrive,
			"export_accounts": self.exportAccounts,
			"import_accounts": self.importAccounts,
			"force_sync_drive": self.forceSyncDrive,
			"force_sync_drives": self.forceSyncDrives,
			"get_sync_settings": self.getSyncSettings,
			"list_accounts": self.listAccounts,
			"list_drive": self.createDriveMenu,
			"list_drives": self.createDrivesMenu,
			"list_folders": self.addFolders,
			"list_shared_drives": self.listSharedDrives,
			"list_synced_folders": self.listSyncedFolders,
			"main": self.createMainMenu,
			"register_account": self.registerAccount,
			"resolution_priority": self.resolutionPriority,
			"search_drive": self.searchDrive,
			"search_folder": self.searchFolder,
			"set_alias": self.setAlias,
			"set_playback_account": self.setPlaybackAccount,
			"set_tmdb_language": self.setTMDBlanguage,
			"set_tmdb_region": self.setTMDBregion,
			"sync_all_folders": self.syncAllFolders,
			"sync_folder": self.syncFolder,
			"sync_multiple_folders": self.syncMultipleFolders,
			"validate_accounts": self.validateAccounts,
			"video": self.playVideo,
		}

		if self.mode == "video":
			modes[self.mode](dbID, dbType, filePath)
		else:
			modes[self.mode]()

		xbmcplugin.endOfDirectory(self.pluginHandle, succeeded=self.succeeded, cacheToDisc=self.cacheToDisk)

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

	def addMenuItem(self, url, title, contextMenu=None, dateTime=None, isFolder=True):
		listItem = xbmcgui.ListItem(title)

		if dateTime:
			listItem.setDateTime(dateTime)

		if contextMenu:
			listItem.addContextMenuItems(contextMenu, True)

		xbmcplugin.addDirectoryItem(self.pluginHandle, url, listItem, isFolder=isFolder)

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

		if not tokenRefresh:
			return

		driveID = self.settings.getParameter("drive_id")
		self.accountManager.addAccount(account, driveID)
		xbmc.executebuiltin("Container.Refresh")

	def createDriveMenu(self):
		driveID = self.settings.getParameter("drive_id")
		account = self.accountManager.getAccount(driveID)

		if not account:
			return

		self.cloudService.setAccount(account)
		self.refreshToken(account.expiry)
		driveSettings = self.cache.getDrive(driveID)

		if driveSettings:
			self.addMenuItem(
				f"{self.pluginURL}?mode=list_synced_folders&drive_id={driveID}",
				f"[COLOR yellow][B]{self.settings.getLocalizedString(30011)}[/B][/COLOR]",
			)

		self.addMenuItem(
			f"{self.pluginURL}?mode=list_accounts&drive_id={driveID}",
			f"[COLOR yellow][B]{self.settings.getLocalizedString(30032)}[/B][/COLOR]",
		)
		self.addMenuItem(
			f"{self.pluginURL}?mode=list_folders&drive_id={driveID}",
			self.settings.getLocalizedString(30038),
		)
		self.addMenuItem(
			f"{self.pluginURL}?mode=list_folders&drive_id={driveID}&shared_with_me=true",
			self.settings.getLocalizedString(30039),
		)
		self.addMenuItem(
			f"{self.pluginURL}?mode=list_shared_drives&drive_id={driveID}",
			self.settings.getLocalizedString(30040),
		)
		self.addMenuItem(
			f"{self.pluginURL}?mode=search_drive&drive_id={driveID}",
			self.settings.getLocalizedString(30041),
		)
		self.addMenuItem(
			f"{self.pluginURL}?mode=list_folders&drive_id={driveID}&starred=true",
			self.settings.getLocalizedString(30042),
		)
		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_LABEL)

	def createDrivesMenu(self):
		self.addMenuItem(
			f"{self.pluginURL}?mode=register_account",
			f"[B][COLOR yellow]{self.settings.getLocalizedString(30207)}[/COLOR][/B]",
			isFolder=False,
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
					f"RunPlugin({self.pluginURL}?mode=force_sync_drive&drive_id={driveID})",
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
			self.addMenuItem(
				f"{self.pluginURL}?mode=list_drive&drive_id={driveID}",
				displayName,
				contextMenu,
			)

		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)

	def createMainMenu(self):
		syncRootPath = self.cache.getSyncRootPath()

		if syncRootPath:
			self.addMenuItem(
				syncRootPath,
				f"[COLOR yellow][B]{self.settings.getLocalizedString(30008)}[/B][/COLOR]",
			)

		contextMenu = [
			(
				self.settings.getLocalizedString(30010),
				f"RunPlugin({self.pluginURL}?mode=force_sync_drives)",
			),
		]
		self.addMenuItem(
			f"{self.pluginURL}?mode=list_drives",
			f"[COLOR yellow][B]{self.settings.getLocalizedString(30085)}[/B][/COLOR]",
			contextMenu,
		)
		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_FILE)
		self.cacheToDisk = False

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
		data = {"drive_id": driveID}
		requester.makeRequest(url, data)

	def exportAccounts(self):
		filePath = self.dialog.browse(0, self.settings.getLocalizedString(30034), "")

		if not filePath:
			return

		self.accountManager.exportAccounts(filePath)
		self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30035))

	def importAccounts(self):
		filePath = self.dialog.browse(1, self.settings.getLocalizedString(30033), "files", mask=".pkl")

		if not filePath:
			return

		imported = self.accountManager.mergeAccounts(filePath)

		if not imported:
			self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30037))
		else:
			self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30036))

	def forceSyncDrive(self):
		driveID = self.settings.getParameter("drive_id")
		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/sync"
		data = {"drive_id": driveID}
		requester.makeRequest(url, data)

	def forceSyncDrives(self):
		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/sync_all"
		requester.makeRequest(url)

	def getFolders(self, driveID, folderID, search=False):
		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.refreshToken(account.expiry)
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
				folderIDs.append(folderID)

				if searchQuery in folderName.lower():
					folders.append({"name": folderName, "id": folderID, "modifiedTime": folder["modifiedTime"]})

		maxIDs = 100
		queries = []

		while folderIDs:
			ids = folderIDs[:maxIDs]
			queries.append(("mimeType='application/vnd.google-apps.folder' and not trashed and (" + " or ".join(f"'{id}' in parents" for id in ids) + ")",))
			folderIDs = folderIDs[maxIDs:]

		with threadpool.threadpool.ThreadPool(threadCount) as pool:
			pool.map(getFolders, queries)

		if folderIDs:
			self.getSpecificFolders(searchQuery, folders, folderIDs, threadCount)

	def getSyncSettings(self):
		driveID = self.settings.getParameter("drive_id")
		folderID = self.settings.getParameter("folder_id")
		folderName = self.settings.getParameter("folder_name")
		mode = self.settings.getParameter("sync_mode")
		self.succeeded = False
		syncSettings = ui.sync_settings.SyncSettings(drive_id=driveID, folder_id=folderID, accounts=self.accounts, folder_name=folderName, mode=mode)
		syncSettings.doModal()
		del syncSettings

	def listAccounts(self):
		driveID = self.settings.getParameter("drive_id")
		account = self.accountManager.getAccount(driveID)

		if not account:
			return

		self.cloudService.setAccount(account)
		self.refreshToken(account.expiry)

		self.addMenuItem(
			f"{self.pluginURL}?mode=add_service_account&drive_id={driveID}",
			f"[B][COLOR yellow]{self.settings.getLocalizedString(30214)}[/COLOR][/B]",
			isFolder=False,
		)
		self.addMenuItem(
			f"{self.pluginURL}?mode=validate_accounts&drive_id={driveID}",
			f"[B][COLOR yellow]{self.settings.getLocalizedString(30021)}[/COLOR][/B]",
			isFolder=False,
		)
		self.addMenuItem(
			f"{self.pluginURL}?mode=delete_accounts&drive_id={driveID}",
			f"[B][COLOR yellow]{self.settings.getLocalizedString(30022)}[/COLOR][/B]",
			isFolder=False,
		)

		for index, account in enumerate(self.accountManager.getAccounts(driveID)):
			accountName = account.name
			self.addMenuItem(
				f"{self.pluginURL}?mode=accounts_cm&account_name={accountName}&account_index={index}&drive_id={driveID}",
				f"[COLOR lime][B]{accountName}[/B][/COLOR]",
				isFolder=False,
			)

		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_LABEL)

	def listFolders(self, driveID, folders, parentFolderID=None):
		sharedWithMe = self.settings.getParameter("shared_with_me")
		starred = self.settings.getParameter("starred")

		for folder in folders:
			folderID = folder["id"]
			folderName = folder["name"]
			modifiedTime = folder["modifiedTime"]
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
					contextMenu = None
				else:
					contextMenu = [
						(
							self.settings.getLocalizedString(30013),
							f"RunPlugin({self.pluginURL}?mode=sync_folder&sync_mode=new&drive_id={driveID}&folder_id={folderID}&folder_name={folderName}&modified_time={modifiedTime})",
						),
						(
							self.settings.getLocalizedString(30090),
							f"RunPlugin({self.pluginURL}?mode=sync_multiple_folders&sync_mode=new&drive_id={driveID}&parent_id={parentFolderID}&shared_with_me={sharedWithMe}&starred={starred})",
						),
						(
							self.settings.getLocalizedString(30010),
							f"RunPlugin({self.pluginURL}?mode=sync_all_folders&sync_mode=new&drive_id={driveID}&parent_id={parentFolderID}&shared_with_me={sharedWithMe}&starred={starred})",
						),
						(
							self.settings.getLocalizedString(30091),
							f"RunPlugin({self.pluginURL}?mode=search_folder&drive_id={driveID}&folder_id={folderID})",
						),
					]

					if self.mode in ("search_folder", "search_drive"):
						contextMenu = contextMenu[:1]

			self.addMenuItem(
				f"{self.pluginURL}?mode=list_folders&drive_id={driveID}&folder_id={folderID}",
				folderName,
				contextMenu,
				dateTime=modifiedTime,
			)

		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_LABEL)
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_DATE)

	def listSharedDrives(self):
		driveID = self.settings.getParameter("drive_id")
		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.refreshToken(account.expiry)
		sharedDrives = self.cloudService.getDrives()

		if not sharedDrives:
			return

		for sharedDrive in sharedDrives:
			sharedDriveID = sharedDrive["id"]
			sharedDriveName = sharedDrive["name"]
			self.addMenuItem(
				f"{self.pluginURL}?mode=list_folders&drive_id={driveID}&shared_drive_id={sharedDriveID}",
				f"[B]{sharedDriveName}[/B]",
			)

	def listSyncedFolders(self):
		driveID = self.settings.getParameter("drive_id")
		folders = self.cache.getFolders({"drive_id": driveID})
		folders = sorted(folders, key=lambda x: x["local_path"].lower())
		self.addMenuItem(
			f"{self.pluginURL}?mode=get_sync_settings&drive_id={driveID}&sync_mode=drive",
			f"[B][COLOR yellow]{self.settings.getLocalizedString(30017)}[/COLOR][/B]",
			isFolder=False,
		)

		for folder in folders:
			folderName = folder["local_path"]
			folderID = folder["folder_id"]
			self.addMenuItem(
				f"{self.pluginURL}?mode=get_sync_settings&drive_id={driveID}&folder_id={folderID}&sync_mode=folder",
				f"[COLOR lime][B]{folderName}[/B][/COLOR]",
			)

		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_FILE)

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
		self.refreshToken(account.expiry)
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
		url = f"http://localhost:{serverPort}/initialize_stream"
		data = {
			"encrypted": encrypted,
			"url": driveURL,
			"drive_id": driveID,
			"file_id": fileID,
			"transcoded": transcoded,
		}
		requester.makeRequest(url, data)
		item = xbmcgui.ListItem(path=f"http://localhost:{serverPort}/play")

		if self.settings.getSetting("subtitles_format") == "Subtitles are named the same as STRM":
			subtitles = glob.glob(glob.escape(filePath.rstrip(".strm")) + "*[!gom]")
			item.setSubtitles(subtitles)
		else:
			subtitles = glob.glob(glob.escape(os.path.dirname(filePath) + os.sep) + "*[!gom]")
			item.setSubtitles(subtitles)

		xbmcplugin.setResolvedUrl(self.pluginHandle, True, item)
		url = f"http://localhost:{serverPort}/start_player"
		data = {"db_id": dbID, "db_type": dbType}
		requester.makeRequest(url, data)

	def refreshToken(self, expiry):
		timeNow = datetime.datetime.now()

		if timeNow >= expiry:
			self.cloudService.refreshToken()
			self.accountManager.saveAccounts()

	def registerAccount(self):
		help = self.dialog.yesno(
			self.settings.getLocalizedString(30000),
			"{} [B][COLOR blue]http://localhost:{}/register[/COLOR][/B] {}\n\n{} [COLOR chartreuse]{}[/COLOR] - [COLOR chartreuse]{}[/COLOR] {} [COLOR chartreuse]{}[/COLOR] [B][COLOR blue]http://localhost:{}/status[/COLOR][/B]".format(
				self.settings.getLocalizedString(30215),
				self.settings.getSetting("server_port"),
				self.settings.getLocalizedString(30216),
				self.settings.getLocalizedString(30217),
				self.settings.getLocalizedString(30218),
				self.settings.getLocalizedString(30219),
				self.settings.getLocalizedString(30220),
				self.settings.getLocalizedString(30221),
				self.settings.getSetting("server_port"),
			),
			self.settings.getLocalizedString(30066),
			self.settings.getLocalizedString(30001),
		)

		if help:
			url = "https://github.com/user-attachments/assets/b3d0e86f-2597-40c8-8485-6d11ad085372"
			listItem = xbmcgui.ListItem("Client ID and Client Secret creation")
			xbmc.Player().play(url, listItem)

	def resolutionPriority(self):
		resolutions = self.settings.getSetting("resolution_priority").split(", ")
		resolutionOrder = ui.resolution_order.ResolutionOrder(resolutions=resolutions)
		resolutionOrder.doModal()
		newOrder = resolutionOrder.priorityList
		del resolutionOrder

		if newOrder:
			self.settings.setSetting("resolution_priority", ", ".join(newOrder))

	def searchDrive(self):
		searchQuery = self.dialog.input(self.settings.getLocalizedString(30043))

		if not searchQuery:
			self.succeeded = False
			return

		driveID = self.settings.getParameter("drive_id")
		folders = self.getFolders(driveID, driveID, search=searchQuery)
		self.listFolders(driveID, folders)

	def searchFolder(self):
		searchQuery = self.dialog.input(self.settings.getLocalizedString(30043))

		if not searchQuery:
			self.succeeded = False
			return

		searchQuery = searchQuery.lower()
		driveID = self.settings.getParameter("drive_id")
		sharedDriveID = self.settings.getParameter("shared_drive_id")
		folderID = self.settings.getParameter("folder_id")
		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.refreshToken(account.expiry)

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

	def setAlias(self):
		driveID = self.settings.getParameter("drive_id")
		alias = self.dialog.input(self.settings.getLocalizedString(30004))

		if not alias:
			return

		xbmc.executebuiltin("ActivateWindow(busydialognocancel)")
		alias = filesystem.helpers.removeProhibitedFSchars(alias)

		if alias in self.accountManager.aliases:
			self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30015))
			return

		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/set_alias"
		data = {"drive_id": driveID, "alias": alias}
		requester.makeRequest(url, data)

	def setPlaybackAccount(self):
		accounts = self.accountManager.getDrives()
		displayNames = [account[1] for account in accounts]
		selection = self.dialog.select(self.settings.getLocalizedString(30014), displayNames)

		if selection == -1:
			return

		self.settings.setSetting("playback_account", accounts[selection][0])
		self.settings.setSetting("account_override", accounts[selection][1])

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

	def showAccountsContextMenu(self):
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

			if not tokenRefresh:
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

	def syncAllFolders(self):
		driveID = self.settings.getParameter("drive_id")
		parentFolderID = self.settings.getParameter("parent_id")
		mode = self.settings.getParameter("sync_mode")
		self.succeeded = False
		folders = self.getFolders(driveID, parentFolderID)
		syncSettings = ui.sync_settings.SyncSettings(drive_id=driveID, accounts=self.accounts, folders=folders, mode=mode)
		syncSettings.doModal()
		del syncSettings

	def syncFolder(self):
		driveID = self.settings.getParameter("drive_id")
		folderID = self.settings.getParameter("folder_id")
		folderName = self.settings.getParameter("folder_name")
		modifiedTime = self.settings.getParameter("modified_time")
		folders = [{"id": folderID, "name": folderName, "modifiedTime": modifiedTime}]
		mode = self.settings.getParameter("sync_mode")
		self.succeeded = False
		syncSettings = ui.sync_settings.SyncSettings(drive_id=driveID, accounts=self.accounts, folders=folders, mode=mode)
		syncSettings.doModal()
		del syncSettings

	def syncMultipleFolders(self):
		driveID = self.settings.getParameter("drive_id")
		parentFolderID = self.settings.getParameter("parent_id")
		mode = self.settings.getParameter("sync_mode")
		self.succeeded = False
		folders = self.getFolders(driveID, parentFolderID)
		folderNames = sorted([(folder["name"], index) for index, folder in enumerate(folders)], key=lambda x: x[0].lower())
		chosenFolders = self.dialog.multiselect(self.settings.getLocalizedString(30086), [name for name, _ in folderNames])

		if not chosenFolders:
			return

		folders = [folders[folderNames[index][1]] for index in chosenFolders]
		syncSettings = ui.sync_settings.SyncSettings(drive_id=driveID, accounts=self.accounts, folders=folders, mode=mode)
		syncSettings.doModal()
		del syncSettings

	def validateAccounts(self):
		driveID = self.settings.getParameter("drive_id")
		accounts = self.accountManager.getAccounts(driveID)
		accountAmount = len(accounts)
		progressDialog = xbmcgui.DialogProgress()
		progressDialog.create(self.settings.getLocalizedString(30306))
		deletion = False
		count = 1

		for account in list(accounts):
			accountName = account.name

			if progressDialog.iscanceled():
				return

			self.cloudService.setAccount(account)
			tokenRefresh = self.cloudService.refreshToken()
			progressDialog.update(int(round(count / accountAmount * 100)), accountName)
			count += 1

			if not tokenRefresh:
				selection = self.dialog.yesno(
					self.settings.getLocalizedString(30000),
					f"{accountName} {self.settings.getLocalizedString(30019)}",
				)

				if not selection:
					continue

				self.accountManager.deleteAccount(driveID, account)
				deletion = True

		progressDialog.close()
		self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30020))

		if deletion:
			xbmc.executebuiltin("Container.Refresh")

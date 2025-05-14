import os
import sys
import json
import time
import datetime

import xbmc
import xbmcgui
import xbmcvfs
import xbmcplugin

from constants import *
from helpers import getElapsedTime, rpc
from .ui.dialogs import Dialog
from .ui.strm_affixer import StrmAffixer
from .ui.sync_settings import SyncSettings
from .ui.resolution_order import ResolutionOrder
from .ui.encryption_settings import EncryptionSettings
from .ui.resolution_selector import ResolutionSelector
from .network import http_requester
from .network.network_helpers import unquote
from .accounts.account import ServiceAccount
from .accounts.account_manager import AccountManager
from .threadpool.threadpool import ThreadPool
from .google_api.google_drive import GoogleDrive
from .sync.sync_cache_manager import SyncCacheManager
from .encryption.profile_manager import ProfileManager
from .filesystem.fs_helpers import removeProhibitedFSchars
from .filesystem.fs_constants import SUBTITLE_EXTENSIONS, TMDB_LANGUAGES, TMDB_REGIONS


class Core:

	def __init__(self):
		self.pluginURL = sys.argv[0]
		self.pluginHandle = int(sys.argv[1])
		self.settings = SETTINGS
		self.mode = self.settings.getParameter("mode", "main")
		self.cache = SyncCacheManager()
		self.accountManager = AccountManager()
		self.accounts = self.accountManager.accounts
		self.cloudService = GoogleDrive()
		self.dialog = Dialog()
		self.succeeded = True
		self.cacheToDisk = True

	def run(self, dbID, dbType, filePath):

		if self.pluginHandle < 0 and self.mode == "search_folder":
			xbmc.executebuiltin(f"Container.Update({self.pluginURL + sys.argv[2]})")
			return

		modes = {
			"accounts_cm": self.showAccountsContextMenu,
			"add_service_account": self.addServiceAccount,
			"create_encryption_profile": self.createEncryptionProfile,
			"delete_accounts": self.deleteAccounts,
			"delete_accounts_file": self.deleteAccountsFile,
			"delete_drive": self.deleteDrive,
			"delete_encryption_profiles": self.deleteEncryptionProfiles,
			"delete_sync_cache": self.deleteSyncCache,
			"delete_sync_folder": self.deleteSyncFolder,
			"export_accounts": self.exportAccounts,
			"export_encryption_profiles": self.exportEncryptionProfiles,
			"force_sync_drive": self.forceSyncDrive,
			"force_sync_drives": self.forceSyncDrives,
			"get_sync_settings": self.getSyncSettings,
			"import_accounts": self.importAccounts,
			"import_encryption_profiles": self.importEncryptionProfiles,
			"list_accounts": self.listAccounts,
			"list_drive": self.createDriveMenu,
			"list_drives": self.createDrivesMenu,
			"list_folders": self.addFolders,
			"list_shared_drives": self.listSharedDrives,
			"list_synced_folders": self.listSyncedFolders,
			"main": self.createMainMenu,
			"modify_encryption_profile": self.modifyEncryptionProfile,
			"register_account": self.registerAccount,
			"resolution_priority": self.resolutionPriority,
			"search_drive": self.searchDrive,
			"search_folder": self.searchFolder,
			"set_alias": self.setAlias,
			"set_default_encryption_profile": self.setDefaultEncryptionProfile,
			"set_encryption_profile": self.setEncryptionProfile,
			"set_playback_account": self.setPlaybackAccount,
			"set_strm_prefix": self.setStrmPrefix,
			"set_strm_suffix": self.setStrmSuffix,
			"set_sync_root": self.setSyncRoot,
			"set_tmdb_language": self.setTMDBlanguage,
			"set_tmdb_region": self.setTMDBregion,
			"set_video_source": self.setVideoSource,
			"sync_all_folders": self.syncAllFolders,
			"sync_folder": self.syncFolder,
			"sync_multiple_folders": self.syncMultipleFolders,
			"validate_accounts": self.validateAccounts,
			"video": lambda: self.playVideo(dbID, dbType, filePath),
		}
		modes[self.mode]()
		xbmcplugin.endOfDirectory(self.pluginHandle, succeeded=self.succeeded, cacheToDisc=self.cacheToDisk)

	def addFolders(self):
		driveID = self.settings.getParameter("drive_id")
		folderID = self.settings.getParameter("folder_id")
		sharedDriveID = self.settings.getParameter("shared_drive_id")

		if not folderID:
			folderID = sharedDriveID or driveID

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
		filePaths = self.dialog.browse(1, 30026, "", mask=".json", enableMultiple=True)

		if not filePaths:
			return

		name = self.dialog.input(30134) if len(filePaths) > 1 else self.dialog.input(30025)

		if not name:
			return

		accounts = []
		driveID = self.settings.getParameter("drive_id")

		for filePath in filePaths:

			with xbmcvfs.File(filePath) as file:
				data = json.loads(file.read())

			email = data.get("client_email")
			key = data.get("private_key")
			error = False

			if not email and not key:
				error = 30028
			elif not email:
				error = 30029
			elif not key:
				error = 30030

			if error:
				self.dialog.ok(f"{self.settings.getLocalizedString(error)} {filePath}")
				continue

			account = ServiceAccount()
			account.name = name
			account.email = email
			account.key = key
			self.cloudService.setAccount(account)
			tokenRefresh = self.cloudService.refreshToken()

			if not tokenRefresh:
				continue

			accounts.append(account)

		self.accountManager.addAccounts(accounts, driveID)
		xbmc.executebuiltin("Container.Refresh")

	def createDriveMenu(self):
		driveID = self.settings.getParameter("drive_id")
		account = self.accountManager.getAccount(driveID)

		if not account:
			self.succeeded = False
			self.dialog.ok(30078)
			return

		driveSettings = self.cache.getDrive(driveID)

		if driveSettings:
			self.addMenuItem(
				f"{self.pluginURL}?mode=list_synced_folders&drive_id={driveID}",
				f"[B][COLOR yellow]{self.settings.getLocalizedString(30011)}[/COLOR][/B]",
			)

		self.addMenuItem(
			f"{self.pluginURL}?mode=list_accounts&drive_id={driveID}",
			f"[B][COLOR yellow]{self.settings.getLocalizedString(30032)}[/COLOR][/B]",
		)
		self.addMenuItem(
			f"{self.pluginURL}?mode=list_folders&drive_id={driveID}",
			f"[B]{self.settings.getLocalizedString(30038)}[/B]",
		)
		self.addMenuItem(
			f"{self.pluginURL}?mode=list_folders&drive_id={driveID}&shared_with_me=true",
			f"[B]{self.settings.getLocalizedString(30039)}[/B]",
		)
		self.addMenuItem(
			f"{self.pluginURL}?mode=list_shared_drives&drive_id={driveID}",
			f"[B]{self.settings.getLocalizedString(30040)}[/B]",
		)
		self.addMenuItem(
			f"{self.pluginURL}?mode=search_drive&drive_id={driveID}",
			f"[B]{self.settings.getLocalizedString(30041)}[/B]",
		)
		self.addMenuItem(
			f"{self.pluginURL}?mode=list_folders&drive_id={driveID}&starred=true",
			f"[B]{self.settings.getLocalizedString(30042)}[/B]",
		)
		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_LABEL)

	def createDrivesMenu(self):
		displayLastSync = self.settings.getSetting("display_last_sync")
		self.addMenuItem(
			f"{self.pluginURL}?mode=register_account",
			f"[B][COLOR yellow]{self.settings.getLocalizedString(30207)}[/COLOR][/B]",
			isFolder=False,
		)

		for driveID, accountData in self.accounts.items():
			alias = accountData["alias"]
			displayName = alias or driveID
			contextMenu = [
				(
					self.settings.getLocalizedString(30500),
					f"RunPlugin({self.pluginURL}?mode=force_sync_drive&drive_id={driveID})",
				),
				(
					self.settings.getLocalizedString(30002),
					f"RunPlugin({self.pluginURL}?mode=set_alias&drive_id={driveID})",
				),
				(
					self.settings.getLocalizedString(30159),
					f"RunPlugin({self.pluginURL}?mode=delete_drive&drive_id={driveID}&drive_name={displayName})",
				)
			]
			self.addMenuItem(
				f"{self.pluginURL}?mode=list_drive&drive_id={driveID}",
				f"[B]{displayName}[/B]{f' | {getElapsedTime(lastSync)}' if displayLastSync and (lastSync := self.cache.getLastSync(driveID)) else ''}",
				contextMenu,
			)

		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)

	def createEncryptionProfile(self):
		encryptionSettings = EncryptionSettings(mode="add")
		encryptionSettings.doModal()
		del encryptionSettings

	def createMainMenu(self):
		syncRootPath = self.cache.getSyncRootPath()

		if syncRootPath:
			self.addMenuItem(
				syncRootPath,
				f"[B][COLOR yellow]{self.settings.getLocalizedString(30008)}[/COLOR][/B]",
			)

		contextMenu = [
			(
				self.settings.getLocalizedString(30010),
				f"RunPlugin({self.pluginURL}?mode=force_sync_drives)",
			),
		]
		self.addMenuItem(
			f"{self.pluginURL}?mode=list_drives",
			f"[B][COLOR yellow]{self.settings.getLocalizedString(30085)}[/COLOR][/B]",
			contextMenu,
		)
		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_FILE)
		self.cacheToDisk = False

	def deleteAccounts(self):
		driveID = self.settings.getParameter("drive_id")
		accounts = self.accountManager.getAccounts(driveID)
		accountNames = self.accountManager.getAccountNames(accounts)
		selection = self.dialog.multiselect(30158, accountNames)

		if not selection:
			return

		deletedAccounts = [accountNames[s] for s in selection]
		self.accountManager.deleteAccounts(deletedAccounts, accounts, driveID)
		xbmc.executebuiltin("Container.Refresh")

	def deleteAccountsFile(self):
		confirmation = self.dialog.yesno(30024)

		if not confirmation:
			return

		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/delete_accounts_file"
		http_requester.request(url)

	def deleteDrive(self):
		driveID = self.settings.getParameter("drive_id")
		driveName = self.settings.getParameter("drive_name")
		confirmation = self.dialog.yesno(f"{self.settings.getLocalizedString(30016)} {driveName}?")

		if not confirmation:
			return

		deleteFiles = self.dialog.yesno(30027)
		self.dialog.notification(f"{self.settings.getLocalizedString(30105)} {driveName}")
		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/delete_drive"
		data = {"drive_id": driveID, "drive_name": driveName, "delete_files": deleteFiles}
		http_requester.request(url, data)

	def deleteEncryptionProfiles(self):
		profileManager = ProfileManager()
		ids, names = profileManager.getProfileEntries()
		selection = self.dialog.multiselect(30129, names)

		if not selection:
			return

		deletedIDs = []

		for idx in selection:
			id = ids[idx]
			profileManager.deleteProfile(id)
			deletedIDs.append(id)

		if self.settings.getSetting("default_encryption_id") in deletedIDs:
			cid = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId()).getFocusId()
			xbmc.executebuiltin("Dialog.Close(all,true)")

			while self.settings.getSetting("default_encryption_id") and self.settings.getSetting("default_encryption_name"):
				self.settings.setSetting("default_encryption_id", "")
				self.settings.setSetting("default_encryption_name", "")
				time.sleep(0.1)

			xbmc.executebuiltin("Addon.OpenSettings(plugin.video.gdrive)")
			xbmc.executebuiltin(f"SetFocus({cid - 19})")
			xbmc.executebuiltin(f"SetFocus({cid})")

		self.dialog.notification(30117 if len(selection) > 1 else 30130)

	def deleteSyncCache(self):
		cid = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId()).getFocusId()
		confirmation = self.dialog.yesno(30054)

		if not confirmation:
			return

		self.dialog.notification(30088)
		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/delete_sync_cache"
		data = {"cid": cid}
		http_requester.request(url, data)

	def deleteSyncFolder(self):
		syncRootCache = self.cache.getSyncRootPath()
		syncRoot = syncRootCache or self.settings.getSetting("sync_root")

		if not syncRoot:
			syncRoot = self.dialog.ok(30092)
			self.settings.setSetting("sync_root", "")
			return

		if not os.path.exists(syncRoot):
			self.dialog.ok(30100)

			if not syncRootCache:
				self.settings.setSetting("sync_root", "")

			return

		cid = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId()).getFocusId()
		confirmation = self.dialog.yesno(30094)

		if not confirmation:
			return

		self.dialog.notification(30074)
		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/delete_sync_folder"
		data = {"sync_root": syncRoot, "cid": cid}
		http_requester.request(url, data)

	def exportAccounts(self):
		dirPath = self.dialog.browse(3, 30034, "")

		if not dirPath:
			return

		filename = self.dialog.input(30099, defaultt="gdrive_accounts")

		if not filename:
			return

		filename = f"{filename}.pkl"
		filePath = os.path.join(dirPath, filename)
		self.accountManager.saveAccounts(filePath)
		self.dialog.ok(f"{self.settings.getLocalizedString(30035)} {filename}")

	def exportEncryptionProfiles(self):
		dirPath = self.dialog.browse(3, 30034, "")

		if not dirPath:
			return

		filename = self.dialog.input(30099, defaultt="gdrive_profiles")

		if not filename:
			return

		filename = f"{filename}.pkl"
		filePath = os.path.join(dirPath, filename)
		profileManager = ProfileManager()
		profileManager.exportProfiles(filePath)
		self.dialog.ok(f"{self.settings.getLocalizedString(30035)} {filename}")

	def forceSyncDrive(self):
		driveID = self.settings.getParameter("drive_id")
		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/sync"
		data = {"drive_id": driveID}
		http_requester.request(url, data)

	def forceSyncDrives(self):
		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/sync_all"
		http_requester.request(url)

	def getFolders(self, driveID, folderID, searchQuery=None):
		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.refreshToken(account.tokenExpiry)
		sharedWithMe = self.settings.getParameter("shared_with_me")
		starred = self.settings.getParameter("starred")
		return self.cloudService.listDirectory(folderID=folderID, sharedWithMe=sharedWithMe, starred=starred, searchQuery=searchQuery)

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

		with ThreadPool(threadCount) as pool:
			pool.map(getFolders, queries)

		if folderIDs:
			self.getSpecificFolders(searchQuery, folders, folderIDs, threadCount)

	def getSyncSettings(self):
		driveID = self.settings.getParameter("drive_id")
		folderID = self.settings.getParameter("folder_id")
		folderName = self.settings.getParameter("folder_name")
		mode = self.settings.getParameter("sync_mode")
		self.succeeded = False
		syncSettings = SyncSettings(drive_id=driveID, folder_id=folderID, folder_name=folderName, accounts=self.accounts, mode=mode)
		syncSettings.doModal()
		del syncSettings

	def importAccounts(self):
		filePath = self.dialog.browse(1, 30033, "", mask=".pkl")

		if not filePath:
			return

		imported = self.accountManager.mergeAccounts(filePath)

		if not imported:
			self.dialog.ok(30037)
		else:
			self.dialog.notification(30036)
			xbmc.executebuiltin("Container.Refresh")

	def importEncryptionProfiles(self):
		filePath = self.dialog.browse(1, 30033, "", mask=".pkl")

		if not filePath:
			return

		profileManager = ProfileManager()
		imported = profileManager.importProfiles(filePath)

		if not imported:
			self.dialog.ok(30118)
		else:
			self.dialog.notification(30119)

	def listAccounts(self):
		driveID = self.settings.getParameter("drive_id")

		if not self.accountManager.getAccount(driveID):
			return

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
				folderName = f"[B][COLOR lime]{folderName}[/COLOR][/B]"
			else:
				directory = self.cache.getDirectory({"folder_id": folderID})

				if directory:
					contextMenu = None
					folderName = f"[B][COLOR springgreen]{folderName}[/COLOR][/B]"
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
					folderName = f"[B]{folderName}[/B]"

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
		self.refreshToken(account.tokenExpiry)
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
				f"{self.pluginURL}?mode=get_sync_settings&drive_id={driveID}&folder_id={folderID}&folder_name={folderName}&sync_mode=folder",
				f"[COLOR lime][B]{folderName}[/B][/COLOR]",
			)

		xbmcplugin.setContent(self.pluginHandle, "files")
		xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_FILE)

	def modifyEncryptionProfile(self):
		profileManager = ProfileManager()
		ids, names = profileManager.getProfileEntries()
		selection = self.dialog.select(30116, names)

		if selection == -1:
			return

		id = ids[selection]
		profile = profileManager.getProfile(id)
		profileName = profile.name
		encryptionSettings = EncryptionSettings(profile=profile, mode="modify")
		encryptionSettings.doModal()
		modified = encryptionSettings.modified
		del encryptionSettings

		if not modified:
			return

		if profileName != profile.name and self.settings.getSetting("default_encryption_id") == id:
			cid = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId()).getFocusId()
			xbmc.executebuiltin("Dialog.Close(all,true)")

			while self.settings.getSetting("default_encryption_name") == profileName:
				self.settings.setSetting("default_encryption_name", profile.name)
				time.sleep(0.1)

			xbmc.executebuiltin("Addon.OpenSettings(plugin.video.gdrive)")
			xbmc.executebuiltin(f"SetFocus({cid - 18})")
			xbmc.executebuiltin(f"SetFocus({cid})")

	def playVideo(self, dbID, dbType, filePath):

		if (not dbID or not dbType) and not filePath:
			timeEnd = time.time() + 1

			while time.time() < timeEnd and (not dbID or not dbType):
				xbmc.executebuiltin("Dialog.Close(busydialog)")
				dbID = xbmc.getInfoLabel("ListItem.DBID")
				dbType = xbmc.getInfoLabel("ListItem.DBTYPE")
				filePath = xbmc.getInfoLabel("ListItem.FileNameAndPath")

		filePath = filePath[:-5]
		filename = os.path.basename(filePath)
		fileID = self.settings.getParameter("file_id")
		driveURL = self.cloudService.getDownloadURL(fileID)
		driveID = self.settings.getParameter("drive_id") or self.settings.getSetting("default_playback_account_id")

		if not driveID:
			self.dialog.ok(30057)
			return

		account = self.accountManager.getAccount(driveID, preferOauth=False)
		self.cloudService.setAccount(account)
		self.refreshToken(account.tokenExpiry)
		transcoded = False

		if self.settings.getParameter("encrypted"):
			encryptionID = self.settings.getSetting("default_encryption_id")
			profileManager = ProfileManager()
			profile = profileManager.getProfile(encryptionID)

			if not profile:
				self.dialog.ok(30120)
				return

		elif encryptionID := self.settings.getParameter("encryption_id"):
			profileManager = ProfileManager()
			profile = profileManager.getProfile(encryptionID)

			if not profile:
				encryptionID = self.settings.getSetting("default_encryption_id")
				profile = profileManager.getProfile(encryptionID)

				if not profile:
					self.dialog.ok(30121)
					return

		else:
			resolutionPrompt = self.settings.getSetting("resolution_prompt")
			resolutionPriority = self.settings.getSetting("resolution_priority").split(", ")

			if resolutionPrompt:
				streams = self.cloudService.getStreams(fileID)

				if streams and len(streams) > 1:
					resolutionSelector = ResolutionSelector(resolutions=streams)
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
			"encryption_id": encryptionID,
			"url": driveURL,
			"drive_id": driveID,
			"file_id": fileID,
			"transcoded": transcoded,
		}
		http_requester.request(url, data)
		item = xbmcgui.ListItem(filename, path=f"http://localhost:{serverPort}/play")

		if self.settings.getSetting("set_subtitles"):
			subtitles = []

			with os.scandir(os.path.dirname(filePath)) as entries:

				if self.settings.getSetting("subtitles_format") == self.settings.getLocalizedString(30305):

					for entry in entries:

						if entry.is_file() and entry.name.lower().endswith(SUBTITLE_EXTENSIONS):
							subtitles.append(entry.path)

				else:

					for entry in entries:

						if entry.is_file():
							name, extension = os.path.splitext(entry.name)

							if name == filename and extension.lstrip(".").lower() in SUBTITLE_EXTENSIONS:
								subtitles.append(entry.path)

			item.setSubtitles(subtitles)

		xbmcplugin.setResolvedUrl(self.pluginHandle, True, item)
		url = f"http://localhost:{serverPort}/start_player"
		data = {"db_id": dbID, "db_type": dbType}
		http_requester.request(url, data)

	def refreshToken(self, expiry):
		timeNow = datetime.datetime.now()

		if timeNow >= expiry:
			self.cloudService.refreshToken()
			self.accountManager.saveAccounts()

	def registerAccount(self):
		help = self.dialog.yesno(
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
			nolabel=self.settings.getLocalizedString(30066),
			yeslabel=self.settings.getLocalizedString(30001),
		)

		if help:
			url = "https://github.com/user-attachments/assets/d9ee3658-76b0-435a-bddd-3f4631fdf19a"
			listItem = xbmcgui.ListItem(self.settings.getLocalizedString(30089))
			xbmc.Player().play(url, listItem)

	def resolutionPriority(self):
		resolutions = self.settings.getSetting("resolution_priority").split(", ")
		resolutionOrder = ResolutionOrder(resolutions=resolutions)
		resolutionOrder.doModal()

		if not resolutionOrder.closed:
			self.settings.setSetting("resolution_priority", ", ".join(resolutionOrder.resolutions))

		del resolutionOrder

	def searchDrive(self):
		searchQuery = self.dialog.input(30043)

		if not searchQuery:
			self.succeeded = False
			return

		driveID = self.settings.getParameter("drive_id")
		folders = self.getFolders(driveID, driveID, searchQuery=searchQuery)
		self.listFolders(driveID, folders)

	def searchFolder(self):
		searchQuery = self.dialog.input(30043)

		if not searchQuery:
			self.succeeded = False
			return

		searchQuery = searchQuery.lower()
		driveID = self.settings.getParameter("drive_id")
		sharedDriveID = self.settings.getParameter("shared_drive_id")
		folderID = self.settings.getParameter("folder_id")
		account = self.accountManager.getAccount(driveID)
		self.cloudService.setAccount(account)
		self.refreshToken(account.tokenExpiry)

		if not folderID:
			folderID = sharedDriveID or driveID

		folders = []
		folderIDs = [folderID]
		threadCount = self.settings.getSettingInt("thread_count", 1)
		self.getSpecificFolders(searchQuery, folders, folderIDs, threadCount)
		self.listFolders(driveID, folders)

	def setAffix(self, affix):
		excluded = ["duration", "extension", "resolution"]
		included = [a for a in self.settings.getSetting(f"strm_{affix.lower()}").split(", ") if a]
		[excluded.remove(include) for include in included]
		strmAffixer = StrmAffixer(included=included, excluded=excluded, title=f"STRM {affix}")
		strmAffixer.doModal()
		closed = strmAffixer.closed
		del strmAffixer

		if closed:
			return

		self.settings.setSetting(f"strm_{affix.lower()}", ", ".join(included))

	def setAlias(self):
		driveID = self.settings.getParameter("drive_id")
		alias = self.dialog.input(30004)

		if not alias:
			return

		xbmc.executebuiltin("ActivateWindow(busydialognocancel)")
		alias = removeProhibitedFSchars(alias)

		if alias in self.accountManager.aliases:
			xbmc.executebuiltin("Dialog.Close(busydialognocancel)")
			self.dialog.ok(30015)
			return

		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/set_alias"
		data = {"drive_id": driveID, "alias": alias}
		http_requester.request(url, data)

	def setDefaultEncryptionProfile(self):
		profileManager = ProfileManager()
		ids, names = profileManager.getProfileEntries()
		ids = ("",) + ids
		names = ("",) + names
		selection = self.dialog.select(30116, names)

		if selection == -1:
			return

		id = ids[selection]
		name = names[selection]
		cid = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId()).getFocusId()
		xbmc.executebuiltin("Dialog.Close(all,true)")

		while self.settings.getSetting("default_encryption_id") != id and self.settings.getSetting("default_encryption_name") != name:
			self.settings.setSetting("default_encryption_id", id)
			self.settings.setSetting("default_encryption_name", name)
			time.sleep(0.1)

		xbmc.executebuiltin("Addon.OpenSettings(plugin.video.gdrive)")
		xbmc.executebuiltin(f"SetFocus({cid - 15})")
		xbmc.executebuiltin(f"SetFocus({cid})")

	def setEncryptionProfile(self):
		profileManager = ProfileManager()
		ids, names = profileManager.getProfileEntries()
		ids = ("",) + ids
		names = ("",) + names
		selection = self.dialog.select(30116, names)

		if selection == -1:
			return

		self.settings.setSetting("encryption_id", ids[selection])
		self.settings.setSetting("encryption_name", names[selection])

	def setPlaybackAccount(self):
		accounts = self.accountManager.getDrives()
		accountNames = [""] + [account[1] for account in accounts]
		selection = self.dialog.select(30014, accountNames)

		if selection == -1:
			return

		accountID, accountName = accounts[selection - 1] if selection else ("", "")
		self.settings.setSetting("default_playback_account_id", accountID)
		self.settings.setSetting("default_playback_account_name", accountName)

	def setStrmPrefix(self):
		self.setAffix("Prefix")

	def setStrmSuffix(self):
		self.setAffix("Suffix")

	def setSyncRoot(self):
		syncRoot = self.cache.getSyncRootPath() or self.settings.getSetting("sync_root")

		if not syncRoot:
			self.dialog.ok(30092)
			self.settings.setSetting("sync_root", "")
			return

		cid = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId()).getFocusId()
		syncRootNew = self.dialog.browse(3, 30093, "local")

		if not syncRootNew:
			return

		syncRootNew = os.path.join(syncRootNew, self.settings.getLocalizedString(30000))

		if syncRoot in syncRootNew:
			self.dialog.ok(30101)
			return
		elif os.path.exists(syncRootNew):
			self.dialog.ok(30102)
			return

		self.dialog.notification(30076)
		serverPort = self.settings.getSettingInt("server_port", 8011)
		url = f"http://localhost:{serverPort}/set_sync_root"
		data = {"sync_root_new": syncRootNew, "sync_root_old": syncRoot, "cid": cid}
		http_requester.request(url, data)

	def setTMDBlanguage(self):
		selection = self.dialog.select(30515, TMDB_LANGUAGES)

		if selection == -1:
			return

		self.settings.setSetting("tmdb_language", TMDB_LANGUAGES[selection])

	def setTMDBregion(self):
		selection = self.dialog.select(30516, TMDB_REGIONS)

		if selection == -1:
			return

		self.settings.setSetting("tmdb_region", TMDB_REGIONS[selection])

	def setVideoSource(self):
		response = rpc({"method": "Files.GetSources", "params": {"media": "video"}})
		sources = response.get("result", {}).get("sources", [])
		listItems = []

		for source in sources:
			file = source["file"]

			if file.startswith("addons://"):
				continue

			if file.startswith("multipath://"):
				paths = [unquote(p) for p in file[len("multipath://"):].split("/") if p]
			else:
				paths = [file]

			for path in paths:
				listItem = xbmcgui.ListItem(source["label"], path)
				listItem.setArt({"thumb": "DefaultFolder.png", "icon": "DefaultFolder.png"})
				listItems.append(listItem)

		selection = self.dialog.select(30072, listItems, useDetails=True)

		if selection == -1:
			return

		self.settings.setSetting("video_source", os.path.normpath(listItems[selection].getLabel2()))

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
			newAccountName = self.dialog.input(30025)

			if not newAccountName or newAccountName == accountName:
				return

			self.accountManager.renameAccount(newAccountName, accountIndex, driveID)

		elif selection == 1:
			self.cloudService.setAccount(account)
			tokenRefresh = self.cloudService.refreshToken()

			if not tokenRefresh:
				selection = self.dialog.yesno(f"{accountName} {self.settings.getLocalizedString(30003)}")

				if not selection:
					return

				self.accountManager.deleteAccount(account, driveID)

			else:
				self.dialog.notification(30019)
				return

		elif selection == 2:
			selection = self.dialog.yesno(f"{self.settings.getLocalizedString(30157)} {accountName}?")

			if not selection:
				return

			self.accountManager.deleteAccount(account, driveID)

		else:
			return

		xbmc.executebuiltin("Container.Refresh")

	def syncAllFolders(self):
		driveID = self.settings.getParameter("drive_id")
		parentFolderID = self.settings.getParameter("parent_id")
		mode = self.settings.getParameter("sync_mode")
		self.succeeded = False
		folders = self.getFolders(driveID, parentFolderID)
		syncSettings = SyncSettings(drive_id=driveID, accounts=self.accounts, folders=folders, mode=mode)
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
		syncSettings = SyncSettings(drive_id=driveID, folder_name=folderName, accounts=self.accounts, folders=folders, mode=mode)
		syncSettings.doModal()
		del syncSettings

	def syncMultipleFolders(self):
		driveID = self.settings.getParameter("drive_id")
		parentFolderID = self.settings.getParameter("parent_id")
		mode = self.settings.getParameter("sync_mode")
		self.succeeded = False
		folders = self.getFolders(driveID, parentFolderID)
		syncedFolders = [folder["folder_id"] for folder in self.cache.getFolders({"drive_id": driveID})]
		folderNames = sorted([(folder["name"], index) for index, folder in enumerate(folders) if folder["id"] not in syncedFolders], key=lambda x: x[0].lower())
		chosenFolders = self.dialog.multiselect(30086, [name for name, _ in folderNames])

		if not chosenFolders:
			return

		folders = [folders[folderNames[index][1]] for index in chosenFolders]
		syncSettings = SyncSettings(drive_id=driveID, accounts=self.accounts, folders=folders, mode=mode)
		syncSettings.doModal()
		del syncSettings

	def validateAccounts(self):
		driveID = self.settings.getParameter("drive_id")
		accounts = self.accountManager.getAccounts(driveID)
		accountAmount = len(accounts)
		progressDialog = xbmcgui.DialogProgress()
		progressDialog.create(self.settings.getLocalizedString(30222))
		deletion = False
		count = 1

		for account in list(accounts):
			accountName = account.name
			progressDialog.update(int(round(count / accountAmount * 100)), accountName)
			self.cloudService.setAccount(account)
			tokenRefresh = self.cloudService.refreshToken()
			count += 1

			if progressDialog.iscanceled():
				return

			if not tokenRefresh:

				if selection := self.dialog.yesno(f"{accountName} {self.settings.getLocalizedString(30003)}"):
					self.accountManager.deleteAccount(account, driveID)
					deletion = True

		progressDialog.close()
		self.dialog.notification(30020)

		if deletion:
			xbmc.executebuiltin("Container.Refresh")

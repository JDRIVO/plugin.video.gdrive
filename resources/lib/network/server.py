import os
import re
import json
import time
import datetime
from threading import Thread
from urllib.parse import unquote_plus
from socketserver import ThreadingMixIn
from http.server import BaseHTTPRequestHandler, HTTPServer

import xbmc
import urllib3

from constants import *
from . import registration
from .network_helpers import parseQuery, parseURL
from ..ui.dialogs import Dialog
from ..accounts.account import OAuthAccount
from ..accounts.account_manager import AccountManager
from ..sync.task_manager import TaskManager
from ..sync.sync_cache_manager import SyncCacheManager
from ..playback.video_player import VideoPlayer
from ..google_api.google_drive import GoogleDrive
from ..encryption.encryption import EncryptionHandler
from ..encryption.encryption_types import EncryptionType
from ..filesystem.file_operations import FileOperations


class ServerRunner(Thread):

	def __init__(self):
		super().__init__()

	def run(self):
		self.server = ThreadedHTTPServer(("", SETTINGS.getSettingInt("server_port", 8011)), ServerHandler)
		self.server.daemon_threads = True

		try:
			self.server.serve_forever()
		except Exception:
			self.shutdown()
			self.server_close()

	def shutdown(self):
		self.server.shutdown()
		self.server.server_close()


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.settings = SETTINGS
		self.monitor = xbmc.Monitor()
		self.http = urllib3.PoolManager()
		self.accountManager = AccountManager()
		self.cloudService = GoogleDrive()
		self.cache = SyncCacheManager()
		self.taskManager = TaskManager(self.settings, self.accountManager)
		self.taskManager.run()
		self.encryptor = EncryptionHandler()
		self.fileOperations = FileOperations()
		self.dialog = Dialog()
		self.shutdownRequest = False
		self.failed = False


class ServerHandler(BaseHTTPRequestHandler):

	def changeAccount(self, accounts):

		for account in accounts[1:]:
			self.server.cloudService.setAccount(account)

			if not self.server.cloudService.refreshToken():
				continue

			if self.server.transcoded:
				self.server.url = self.server.cloudService.getStreams(self.server.fileID, (self.server.transcoded,))[1]

			try:
				response = self.server.http.request("HEAD", self.server.url, headers=self.server.cloudService.getHeaders())

				if response.status >= 400:
					continue

			except urllib3.exceptions.HTTPError as e:
				continue

			self.server.dialog.notification(30007)
			accounts.remove(account)
			accounts.insert(0, account)
			self.server.accountManager.saveAccounts()
			return True

	def do_GET(self):
		pathHandlers = {
			"/play": self.handlePlayRequest,
			"/delete_accounts_file": self.handleDeleteAccountsFile,
			"/register": self.handleRegisterRequest,
			"/registration_failed": self.handleRegistrationFailed,
			"/registration_succeeded": self.handleRegistrationSucceeded,
			"/sync_all": self.handleSyncAll,
			"/status": lambda: self.handleStatusRequest(query),
		}
		parsedURL = parseURL(self.path)
		path = parsedURL["path"]
		query = parsedURL["query"]
		handler = pathHandlers.get(path)

		if handler:
			handler()
		else:
			self.send_error(404)

	def do_HEAD(self):

		try:
			response = self.server.http.request("HEAD", self.server.url, headers=self.server.cloudService.getHeaders())

			if response.status >= 400:
				raise urllib3.exceptions.HTTPError({"status": response.status, "reason": response.reason})

		except urllib3.exceptions.HTTPError as e:
			args = args[0] if (args := e.args) else {}
			status = int(args.get("status", 0))
			self.server.failed = True
			accounts = self.server.accountManager.getAccounts(self.server.driveID)

			if not self.changeAccount(accounts):
				self.send_error(400)

				if status == 401:
					message = f"{self.server.settings.getLocalizedString(30018)} {self.server.account.name}"
				elif status == 404:
					message = f"{self.server.settings.getLocalizedString(30209)} {self.server.account.name}"
				elif status in (403, 429):
					message = f"{self.server.settings.getLocalizedString(30006)} {self.server.settings.getLocalizedString(30009)}"
				else:
					message = None
					xbmc.log(f"gdrive error: {e}", xbmc.LOGERROR)

				if message:
					xbmc.executebuiltin("Dialog.Close(all,true)")
					time.sleep(1)
					xbmc.executebuiltin("Dialog.Close(all,true)")
					self.server.dialog.ok(message)

				return

		self.server.failed = False
		self.server.length = int(response.headers.get("Content-Length"))
		self.handleResponse(200, {
			"Content-Length": self.server.length,
			"Content-Type": response.headers.get("Content-Type"),
			"Cache-Control": response.headers.get("Cache-Control"),
			"Date": response.headers.get("Date"),
			"Accept-Ranges": "bytes",
		})

	def do_POST(self):
		pathHandlers = {
			"/add_sync_task": self.handleAddSyncTask,
			"/delete_drive": self.handleDeleteDrive,
			"/delete_sync_cache": self.handleDeleteSyncCache,
			"/delete_sync_folder": self.handleDeleteSyncFolder,
			"/initialize_stream": self.handleInitializeStream,
			"/register": self.handleAccountRegistration,
			"/reset_task": self.handleResetTask,
			"/set_alias": self.handleSetAlias,
			"/set_sync_root": self.handleSetSyncRoot,
			"/start_player": self.handleStartPlayer,
			"/stop_syncing_folders": self.handleStopSyncingFolders,
			"/sync": self.handleSync,
		}
		handler = pathHandlers.get(self.path)

		if handler:
			handler()
		else:
			self.send_error(404)

	def getPostData(self):
		contentLength = int(self.headers["Content-Length"])
		return self.rfile.read(contentLength).decode("utf-8")

	def getPostDataJSON(self):
		return json.loads(self.getPostData())

	def handleAccountRegistration(self):
		queries = parseQuery(self.getPostData())
		clientID = queries["client_id"]
		authURL = self.server.cloudService.getAuthURL(clientID, self.server.server_port)
		self.server.account = OAuthAccount()
		self.server.account.name = unquote_plus(queries["account"])
		self.server.account.clientID = clientID
		self.server.account.clientSecret = queries["client_secret"]
		self.sendRedirect(authURL)

	def handleAddSyncTask(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		driveID = postData[0]
		folders = postData[1:]
		self.server.taskManager.addTask(driveID, folders)

	def handleDeleteAccountsFile(self):
		self.handleResponse(200)
		deleted = self.server.fileOperations.deleteFile(filePath=os.path.join(ADDON_PATH, "accounts.pkl"))

		if deleted:
			self.server.accountManager.setAccounts()
			self.server.dialog.ok(30097)
			xbmc.executebuiltin("Container.Refresh")
		else:
			self.server.dialog.ok(30098)

	def handleDeleteDrive(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		driveID = postData["drive_id"]
		driveName = postData["drive_name"]
		deleteFiles = postData["delete_files"]
		self.server.taskManager.removeTask(driveID)

		if deleteFiles:
			self.server.cache.removeFoldersAndFiles(driveID=driveID)
		else:
			self.server.cache.removeFolders(driveID=driveID)

		self.server.cache.deleteDrive(driveID)
		self.server.accountManager.deleteDrive(driveID)
		self.server.dialog.notification(f"{self.server.settings.getLocalizedString(30106)} {driveName}")
		xbmc.executebuiltin("Container.Refresh")

	def handleDeleteSyncCache(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		cid = postData["cid"]
		self.server.taskManager.removeAllTasks()
		syncRoot = self.server.cache.getSyncRootPath() or self.server.settings.getSetting("sync_root")

		for _ in range(3):
			deleted = self.server.fileOperations.deleteFile(filePath=os.path.join(ADDON_PATH, "sync_cache.db"))

			if deleted:
				break

			time.sleep(0.1)

		if not deleted:
			self.server.dialog.ok(30056)
			return

		self.server.cache.createTables()

		if syncRoot and not os.path.exists(syncRoot):
			xbmc.executebuiltin("Dialog.Close(all,true)")

			while self.server.settings.getSetting("sync_root"):
				self.server.settings.setSetting("sync_root", "")
				time.sleep(0.1)

			xbmc.executebuiltin("Addon.OpenSettings(plugin.video.gdrive)")
			xbmc.executebuiltin(f"SetFocus({cid - 21})")
			xbmc.executebuiltin(f"SetFocus({cid})")

		self.server.dialog.ok(30055)

	def handleDeleteSyncFolder(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		syncRoot = postData["sync_root"]
		cid = postData["cid"]
		self.server.taskManager.removeAllTasks()
		deleted = self.server.fileOperations.deleteFolder(syncRoot)

		if not deleted:
			self.server.dialog.notification(30096)
		else:

			if not self.server.cache.getSyncRootPath():
				xbmc.executebuiltin("Dialog.Close(all,true)")

				while self.server.settings.getSetting("sync_root"):
					self.server.settings.setSetting("sync_root", "")
					time.sleep(0.1)

				xbmc.executebuiltin("Addon.OpenSettings(plugin.video.gdrive)")
				xbmc.executebuiltin(f"SetFocus({cid - 22})")
				xbmc.executebuiltin(f"SetFocus({cid})")

			self.server.dialog.notification(30095)

		self.server.taskManager.run()

	def handleInitializeStream(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		self.server.failed = False
		self.server.url = postData["url"]
		self.server.driveID = postData["drive_id"]
		self.server.fileID = postData["file_id"]
		self.server.transcoded = postData["transcoded"]
		encryptionID = postData["encryption_id"]

		if encryptionID:
			self.server.encryptedStream = True
			self.server.encryptor.setEncryptor(encryptionID)
		else:
			self.server.encryptedStream = False

		self.server.accountManager.setAccounts()
		self.server.account = self.server.accountManager.getAccount(self.server.driveID, preferOauth=False)
		self.server.cloudService.setAccount(self.server.account)

	def handlePlayRequest(self):

		if self.server.failed:
			return

		match = re.search("bytes=(\d+)-(\d*)", self.headers["range"])
		start = int(match.group(1)) if match else ""
		end = int(match.group(2)) if match and match.group(2) else ""
		headers = self.server.cloudService.getHeaders()
		blockIndex = 0
		blockOffset = 0
		chunkOffset = 0

		if start != "":
			range = start

			if self.server.encryptedStream:

				if self.server.encryptor.type == EncryptionType.GDRIVE:

					if start > 16 and end == "":
						chunkOffset = 16 - ((self.server.length - start) % 16) + 8
						range = start - chunkOffset

				else:
					magicSize = 8
					nonceSize = 24
					blockHeaderSize = 16
					blockDataSize = 64 * 1024
					blockTotalSize = blockHeaderSize + blockDataSize
					remainder = start % blockTotalSize

					if remainder:
						blockIndex = start // blockDataSize
						blockOffset = start % blockDataSize
						range = magicSize + nonceSize + (blockIndex * blockTotalSize)

			headers["Range"] = f"bytes={range}-{end}"

		try:
			response = self.server.http.request("GET", self.server.url, headers=headers, preload_content=False)
		except urllib3.exceptions.HTTPError as e:
			log(f"gdrive error: {e}", xbmc.LOGERROR)
			return

		self.sendPlayResponse(start, end, response, blockIndex, blockOffset, chunkOffset)

	def handleRegisterRequest(self):
		self.handleResponse(200, data=registration.form)

	def handleRegistrationFailed(self):
		self.handleResponse(200, data=registration.status(self.server.settings.getLocalizedString(30047)))

	def handleRegistrationSucceeded(self):
		self.handleResponse(200, data=registration.status(self.server.settings.getLocalizedString(30046)))
		xbmc.executebuiltin("Dialog.Close(all,true)")
		xbmc.executebuiltin("Container.Refresh")

	def handleResetTask(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		self.server.taskManager.resetTask(postData["drive_id"])

	def handleResponse(self, code, headers=None, data=None):
		self.send_response(code)

		if headers:
			[self.send_header(header, value) for header, value in headers.items()]

		self.end_headers()

		if data:
			self.wfile.write(data.encode("utf-8"))

	def handleSetAlias(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		driveID = postData["drive_id"]
		alias = postData["alias"]
		self.server.accountManager.setAccounts()
		self.server.accountManager.setAlias(alias, driveID)
		driveSettings = self.server.cache.getDrive(driveID)

		if not driveSettings:
			xbmc.executebuiltin("Dialog.Close(busydialognocancel)")
			xbmc.executebuiltin("Container.Refresh")
			return

		syncRootPath = self.server.cache.getSyncRootPath()
		drivePathOld = os.path.join(syncRootPath, driveSettings["local_path"])
		drivePathNew = os.path.join(syncRootPath, alias)
		self.server.taskManager.removeTask(driveID)
		self.server.cache.updateDrive({"local_path": alias}, driveID)
		self.server.fileOperations.renameFolder(syncRootPath, drivePathOld, drivePathNew)
		self.server.taskManager.spawnTask(driveSettings, startUpRun=False)
		xbmc.executebuiltin("Dialog.Close(busydialognocancel)")
		xbmc.executebuiltin("Container.Refresh")

	def handleSetSyncRoot(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		newSyncPath = postData["sync_root_new"]
		oldSyncPath = postData["sync_root_old"]
		cid = postData["cid"]
		self.server.taskManager.removeAllTasks()
		self.server.cache.updateSyncRootPath(newSyncPath)
		xbmc.executebuiltin("Dialog.Close(all,true)")

		while self.server.settings.getSetting("sync_root") != newSyncPath:
			self.server.settings.setSetting("sync_root", newSyncPath)
			time.sleep(0.1)

		xbmc.executebuiltin("Addon.OpenSettings(plugin.video.gdrive)")
		xbmc.executebuiltin(f"SetFocus({cid - 20})")
		xbmc.executebuiltin(f"SetFocus({cid})")

		if os.path.exists(oldSyncPath):
			self.server.fileOperations.renameFolder(newSyncPath, oldSyncPath, newSyncPath, deleteEmptyDirs=False)
			self.server.dialog.ok(30031)

		self.server.taskManager.run()

	def handleStartPlayer(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		dbID = postData["db_id"]
		dbType = postData["db_type"]
		player = VideoPlayer(dbID, dbType)

		while not self.server.monitor.abortRequested() and not player.close:

			if datetime.datetime.now() >= self.server.cloudService.account.tokenExpiry:
				self.server.cloudService.refreshToken()

				if self.server.transcoded:
					self.server.url = self.server.cloudService.getStreams(self.server.fileID, (self.server.transcoded,))[1]

			if self.server.monitor.waitForAbort(1):
				break

	def handleStatusRequest(self, query):
		code = query.get("code")

		if not code:
			xbmc.log("gdrive error: Google authorization code not returned", xbmc.LOGERROR)
			return

		redirect = "/registration_failed"
		tokens = self.server.cloudService.getToken(self.server.account.clientID, self.server.account.clientSecret, code, self.server.server_port)

		if not tokens:
			xbmc.log("gdrive error: Failed to generate access and refresh tokens", xbmc.LOGERROR)
		else:
			self.server.account.accessToken = tokens["access_token"]
			self.server.account.refreshToken = tokens["refresh_token"]
			self.server.cloudService.setAccount(self.server.account)
			self.server.cloudService.refreshToken()
			driveID = self.server.cloudService.getDriveID()

			if not driveID:
				xbmc.log("gdrive error: Failed to obtain Drive ID", xbmc.LOGERROR)
			else:
				self.server.accountManager.setAccounts()
				self.server.accountManager.addAccount(self.server.account, driveID)
				redirect = "/registration_succeeded"

		self.sendRedirect(f"http://localhost:{self.server.server_port}{redirect}")

	def handleStopSyncingFolders(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		driveID = postData["drive_id"]
		folders = postData.get("folders")
		deleteFiles = postData["delete_files"]
		xbmc.executebuiltin("Container.Refresh")
		self.server.taskManager.removeTask(driveID)

		if deleteFiles:
			self.server.cache.removeFoldersAndFiles(folders, driveID)
		else:
			self.server.cache.removeFolders(folders, driveID)

		self.server.taskManager.spawnTask(self.server.cache.getDrive(driveID), startUpRun=False)

	def handleSync(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		driveID = postData["drive_id"]
		drive = self.server.cache.getDrive(driveID)

		if not drive:
			return

		synced = self.server.taskManager.sync(driveID)

		if synced:
			id = 30044
		else:
			id = 30133

		self.server.dialog.notification(id)

	def handleSyncAll(self):
		self.handleResponse(200)
		synced = self.server.taskManager.syncAll()

		if all(synced):
			id = 30131
		elif any(synced):
			id = 30132
		else:
			id = 30133

		self.server.dialog.notification(id)

	def sendPlayResponse(self, start, end, response, blockIndex, blockOffset, chunkOffset):
		headers = {
			"Content-Type": response.headers.get("Content-Type"),
			"Cache-Control": response.headers.get("Cache-Control"),
			"Date": response.headers.get("Date"),
			"Accept-Ranges": "bytes",
		}

		if start == "":
			headers["Content-Length"] = response.headers.get("Content-Length")
			self.handleResponse(200, headers)
		else:
			headers["Content-Length"] = str(int(response.headers.get("Content-Length")) - chunkOffset)

			if end == "":
				headers["Content-Range"] = f"bytes {start}-{self.server.length - 1}/{self.server.length}"
			else:
				headers["Content-Range"] = f"bytes {start}-{end}/{self.server.length}"

			self.handleResponse(206, headers)

		try:
			self.streamResponse(response, blockIndex, blockOffset, chunkOffset)
		except Exception:
			pass

		response.release_conn()

	def sendRedirect(self, location):
		self.send_response(303)
		self.send_header("Location", location)
		self.end_headers()

	def streamResponse(self, response, blockIndex, blockOffset, chunkOffset):

		if self.server.encryptedStream:

			if self.server.encryptor.type == EncryptionType.GDRIVE:
				self.server.encryptor.decryptStream(response, self.wfile, chunkOffset)
			else:
				self.server.encryptor.decryptStream(response, self.wfile, blockIndex, blockOffset)

		else:
			chunkSize = 16 * 1024

			while chunk := response.read(chunkSize):
				self.wfile.write(chunk)

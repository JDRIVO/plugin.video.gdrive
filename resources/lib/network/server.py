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
from ..accounts.account import Account
from ..accounts.account_manager import AccountManager
from ..sync.task_manager import TaskManager
from ..sync.sync_cache_manager import SyncCacheManager
from ..encryption.encryptor import Encryptor
from ..playback.video_player import VideoPlayer
from ..google_api.google_drive import GoogleDrive
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
		self.fileOperations = FileOperations()
		self.dialog = Dialog()
		self.shutdownRequest = False
		self.failed = False


class ServerHandler(BaseHTTPRequestHandler):

	def decryptStream(self, response, startOffset):
		decrypt = Encryptor(self.server.settings.getSetting("crypto_salt"), self.server.settings.getSetting("crypto_password"))

		try:
			decrypt.decryptStreamChunk(response, self.wfile, startOffset=startOffset)
		except Exception as e:
			xbmc.log(str(e))

	def getPostData(self):
		contentLength = int(self.headers["Content-Length"])
		return self.rfile.read(contentLength).decode("utf-8")

	def getPostDataJSON(self):
		return json.loads(self.getPostData())

	def handleAccountRegistration(self):
		queries = parseQuery(self.getPostData())
		clientID = queries["client_id"]
		authURL = self.server.cloudService.getAuthURL(clientID, self.server.server_port)
		self.server.account = Account()
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
			self.server.dialog.ok(self.server.settings.getLocalizedString(30000), self.server.settings.getLocalizedString(30097))
			xbmc.executebuiltin("Container.Refresh")
		else:
			self.server.dialog.ok(self.server.settings.getLocalizedString(30000), self.server.settings.getLocalizedString(30098))

	def handleDeleteDrive(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		driveID = postData["drive_id"]
		driveName = postData["drive_name"]
		deleteFiles = postData["delete_files"]
		self.server.taskManager.removeTask(driveID)
		self.server.cache.deleteDrive(driveID, deleteFiles)
		self.server.accountManager.deleteDrive(driveID)
		self.server.dialog.notification(self.server.settings.getLocalizedString(30000), f"{self.server.settings.getLocalizedString(30106)} {driveName}")
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
			self.server.dialog.ok(self.server.settings.getLocalizedString(30000), self.server.settings.getLocalizedString(30056))
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

		self.server.dialog.ok(self.server.settings.getLocalizedString(30000), self.server.settings.getLocalizedString(30055))

	def handleDeleteSyncFolder(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		syncRoot = postData["sync_root"]
		cid = postData["cid"]
		self.server.taskManager.removeAllTasks()
		deleted = self.server.fileOperations.deleteFolder(syncRoot)

		if not deleted:
			self.server.dialog.ok(self.server.settings.getLocalizedString(30000), self.server.settings.getLocalizedString(30096))
		else:

			if not self.server.cache.getSyncRootPath():
				xbmc.executebuiltin("Dialog.Close(all,true)")

				while self.server.settings.getSetting("sync_root"):
					self.server.settings.setSetting("sync_root", "")
					time.sleep(0.1)

				xbmc.executebuiltin("Addon.OpenSettings(plugin.video.gdrive)")
				xbmc.executebuiltin(f"SetFocus({cid - 22})")
				xbmc.executebuiltin(f"SetFocus({cid})")

			self.server.dialog.ok(self.server.settings.getLocalizedString(30000), self.server.settings.getLocalizedString(30095))

		self.server.taskManager.run()

	def handleInitializeStream(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		self.server.failed = False
		self.server.url = postData["url"]
		self.server.driveID = postData["drive_id"]
		self.server.fileID = postData["file_id"]
		self.server.encrypted = postData["encrypted"]
		self.server.transcoded = postData["transcoded"]
		self.server.accountManager.setAccounts()
		account = self.server.accountManager.getAccount(self.server.driveID)
		self.server.cloudService.setAccount(account)

	def handlePlayRequest(self):

		if self.server.failed:
			return

		try:
			start, end = re.search("([\d]+)-([\d]*)", self.headers["range"]).group(1, 2)
			start = int(start) if start else ""
			end = int(end) if end else ""
		except AttributeError:
			start = ""
			end = ""

		startOffset = 0
		headers = self.server.cloudService.getHeaders()

		if start:

			if self.server.encrypted and start > 16 and not end:
				startOffset = 16 - ((self.server.length - start) % 16) + 8

			headers["Range"] = f"bytes={start - startOffset}-{end}"

		try:
			response = self.server.http.request("GET", self.server.url, headers=headers, preload_content=False)
		except urllib3.exceptions.HTTPError as e:
			log(f"gdrive error: {e}", xbmc.LOGERROR)
			return

		self.sendPlayResponse(start, end, response, startOffset)

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

			for header, value in headers.items():
				self.send_header(header, value)

		self.end_headers()

		if data:
			self.wfile.write(data.encode("utf-8"))

	def handleSetAlias(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		driveID = postData["drive_id"]
		alias = postData["alias"]
		self.server.accountManager.setAccounts()
		self.server.accountManager.setAlias(driveID, alias)
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
			self.server.dialog.ok(
				self.server.settings.getLocalizedString(30000),
				self.server.settings.getLocalizedString(30031),
			)

		self.server.taskManager.run()

	def handleStartPlayer(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		dbID = postData["db_id"]
		dbType = postData["db_type"]
		player = VideoPlayer(dbID, dbType)

		while not self.server.monitor.abortRequested() and not player.close:

			if datetime.datetime.now() >= self.server.cloudService.account.expiry:

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

	def handleStopSyncingFolder(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		driveID = postData["drive_id"]
		delete = postData["delete"]
		xbmc.executebuiltin("Container.Refresh")
		self.server.taskManager.removeTask(driveID)
		self.server.cache.removeFolder(postData["folder_id"], deleteFiles=delete)
		self.server.taskManager.spawnTask(self.server.cache.getDrive(driveID), startUpRun=False)

		if delete:
			self.server.dialog.notification(
				self.server.settings.getLocalizedString(30000),
				self.server.settings.getLocalizedString(30045),
			)

	def handleStopSyncingFolders(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		driveID = postData["drive_id"]
		delete = postData["delete"]
		xbmc.executebuiltin("Container.Refresh")
		self.server.taskManager.removeTask(driveID)
		self.server.cache.removeFolders(driveID, deleteFiles=delete)

		if delete:
			self.server.dialog.notification(
				self.server.settings.getLocalizedString(30000),
				self.server.settings.getLocalizedString(30045),
			)

	def handleSync(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		driveID = postData["drive_id"]
		drive = self.server.cache.getDrive(driveID)

		if not drive:
			return

		synced = self.server.taskManager.sync(driveID)

		if synced:
			self.server.dialog.notification(
				self.server.settings.getLocalizedString(30000),
				self.server.settings.getLocalizedString(30044),
			)

	def handleSyncAll(self):
		self.handleResponse(200)
		synced = self.server.taskManager.syncAll()

		if synced:
			self.server.dialog.notification(
				self.server.settings.getLocalizedString(30000),
				self.server.settings.getLocalizedString(30044),
			)

	def sendPlayResponse(self, start, end, response, startOffset):
		headers = {
			"Content-Type": response.headers.get("Content-Type"),
			"Cache-Control": response.headers.get("Cache-Control"),
			"Date": response.headers.get("Date"),
			"Accept-Ranges": "bytes",
		}

		if start:
			headers["Content-Length"] = str(int(response.headers.get("Content-Length")) - startOffset)
			headers["Content-Range"] = f"bytes {start}-{end}/{self.server.length}" if end else f"bytes {start}-{self.server.length - 1}/{self.server.length}",
			self.handleResponse(206, headers)
		else:
			headers["Content-Length"] = response.headers.get("Content-Length")
			self.handleResponse(200, headers)

		if self.server.encrypted:
			self.decryptStream(response, startOffset)
		else:
			self.streamResponse(response)

		response.release_conn()

	def sendRedirect(self, location):
		self.send_response(303)
		self.send_header("Location", location)
		self.end_headers()

	def streamResponse(self, response):
		chunkSize = 16 * 1024

		try:

			for chunk in response.stream(chunkSize):
				self.wfile.write(chunk)

		except Exception as e:
			xbmc.log(str(e))

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
				raise urllib3.exceptions.HTTPError({"status": response.status})

		except urllib3.exceptions.HTTPError as e:
			args = args[0] if (args := e.args) else {}
			statusCode = args.get("status")
			self.server.failed = True

			if statusCode == 404:
				self.server.dialog.ok(self.server.settings.getLocalizedString(30003), self.server.settings.getLocalizedString(30209))
				return
			elif statusCode == 401:
				self.server.dialog.ok(self.server.settings.getLocalizedString(30003), self.server.settings.getLocalizedString(30018))
				return
			elif statusCode in (403, 429):
				accountChange = False
				accounts = self.server.accountManager.getAccounts(self.server.driveID)

				for account in accounts[1:]:
					self.server.cloudService.setAccount(account)
					tokenRefresh = self.server.cloudService.refreshToken()

					if not tokenRefresh:
						continue

					if self.server.transcoded:
						self.server.url = self.server.cloudService.getStreams(self.server.fileID, (self.server.transcoded,))[1]

					try:
						response = self.server.http.request("HEAD", self.server.url, headers=self.server.cloudService.getHeaders())

						if response.status >= 400:
							raise urllib3.exceptions.HTTPError({"status": response.status})

					except urllib3.exceptions.HTTPError as e:
						continue

					accountChange = True
					self.server.dialog.notification(
						f"{self.server.settings.getLocalizedString(30003)}: {self.server.settings.getLocalizedString(30006)}",
						self.server.settings.getLocalizedString(30007),
					)
					break

				if not accountChange:
					self.server.dialog.ok(
						f"{self.server.settings.getLocalizedString(30003)}: {self.server.settings.getLocalizedString(30006)}",
						self.server.settings.getLocalizedString(30009),
					)
					return
				else:
					accounts.remove(account)
					accounts.insert(0, account)
					self.server.accountManager.saveAccounts()

			else:
				xbmc.log(f"gdrive error: {e}", xbmc.LOGERROR)
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
			"/stop_syncing_folder": self.handleStopSyncingFolder,
			"/stop_syncing_folders": self.handleStopSyncingFolders,
			"/sync": self.handleSync,
		}
		handler = pathHandlers.get(self.path)

		if handler:
			handler()
		else:
			self.send_error(404)

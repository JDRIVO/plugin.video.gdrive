import os
import re
import json
import time
import datetime
from threading import Thread
from urllib.error import URLError
from urllib.parse import unquote_plus
from urllib.request import Request, urlopen
from socketserver import ThreadingMixIn
from http.server import BaseHTTPRequestHandler, HTTPServer

import xbmc

from constants import SETTINGS
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

	def createRequest(self, start, end, startOffset):

		if start == "":
			return Request(self.server.url, headers=self.server.cloudService.getHeaders())
		else:
			return Request(
				self.server.url,
				headers=self.server.cloudService.getHeaders(
					additionalHeader="Range",
					additionalValue=f"bytes={start - startOffset}-{end}",
				)
			)

	def decryptStream(self, response, startOffset):
		decrypt = Encryptor(self.server.settings.getSetting("crypto_salt"), self.server.settings.getSetting("crypto_password"))

		try:
			decrypt.decryptStreamChunkOld(response, self.wfile, startOffset=startOffset)
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

	def handleDeleteDrive(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		driveID = postData["drive_id"]
		self.server.taskManager.removeTask(driveID)
		self.server.cache.deleteDrive(driveID)
		self.server.accountManager.deleteDrive(driveID)
		xbmc.executebuiltin("Dialog.Close(busydialognocancel)")
		xbmc.executebuiltin("Container.Refresh")

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

		if self.server.encrypted and start != "" and start > 16 and end == "":
			startOffset = 16 - ((int(self.server.length) - start) % 16) + 8

		req = self.createRequest(start, end, startOffset)

		try:
			response = urlopen(req)
		except URLError as e:
			xbmc.log(f"gdrive error: {e}", xbmc.LOGERROR)
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
		self.server.accountManager.setAlias(driveID, alias)
		driveSettings = self.server.cache.getDrive(driveID)

		if not driveSettings:
			xbmc.executebuiltin("Dialog.Close(busydialognocancel)")
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
		self.server.taskManager.removeAllTasks()

		if os.path.exists(oldSyncPath):
			self.server.fileOperations.renameFolder(newSyncPath, oldSyncPath, newSyncPath, deleteEmptyDirs=False)
			self.server.dialog.ok(
				self.server.settings.getLocalizedString(30000),
				self.server.settings.getLocalizedString(30031),
			)

		self.server.cache.updateSyncRootPath(newSyncPath)

		while self.server.settings.getSetting("sync_root") != newSyncPath:
			self.server.settings.setSetting("sync_root", newSyncPath)
			time.sleep(0.1)

		self.server.taskManager.run()

	def handleStartPlayer(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		dbID = postData["db_id"]
		dbType = postData["db_type"]
		trackProgress = dbID is not None
		player = VideoPlayer(dbID, dbType, trackProgress)

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
		delete = postData["delete"]
		xbmc.executebuiltin("Container.Refresh")
		self.server.cache.removeFolder(postData["folder_id"], deleteFiles=delete)

		if delete:
			self.server.dialog.notification(
				self.server.settings.getLocalizedString(30000),
				self.server.settings.getLocalizedString(30045),
			)

	def handleStopSyncingFolders(self):
		postData = self.getPostDataJSON()
		self.handleResponse(200)
		delete = postData["delete"]
		xbmc.executebuiltin("Container.Refresh")
		self.server.cache.removeFolders(postData["drive_id"], deleteFiles=delete)

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

		if start == "":
			self.handleResponse(200, {
				"Content-Length": response.info().get("Content-Length"),
				"Content-Type": response.info().get("Content-Type"),
				"Cache-Control": response.info().get("Cache-Control"),
				"Date": response.info().get("Date"),
				"Accept-Ranges": "bytes",
			})
		else:
			self.handleResponse(206, {
				"Content-Length": str(int(response.info().get("Content-Length")) - startOffset),
				"Content-Range": f"bytes {start}-{end}/{self.server.length}" if end else f"bytes {start}-{int(self.server.length) - 1}/{self.server.length}",
				"Content-Type": response.info().get("Content-Type"),
				"Cache-Control": response.info().get("Cache-Control"),
				"Date": response.info().get("Date"),
				"Accept-Ranges": "bytes",
			})

		if self.server.encrypted:
			self.decryptStream(response, startOffset)
		else:
			self.streamResponse(response)

		response.close()

	def sendRedirect(self, location):
		self.send_response(303)
		self.send_header("Location", location)
		self.end_headers()

	def streamResponse(self, response):
		CHUNK = 16 * 1024

		try:

			while True:
				chunk = response.read(CHUNK)

				if not chunk:
					break

				self.wfile.write(chunk)

		except Exception as e:
			xbmc.log(str(e))

	def do_GET(self):
		pathHandlers = {
			"/play": self.handlePlayRequest,
			"/register": self.handleRegisterRequest,
			"/registration_failed": self.handleRegistrationFailed,
			"/registration_succeeded": self.handleRegistrationSucceeded,
			"/sync_all": self.handleSyncAll,
			"/status": self.handleStatusRequest,
		}
		parsedURL = parseURL(self.path)
		path = parsedURL["path"]
		query = parsedURL["query"]
		handler = pathHandlers.get(path)

		if "/status" in path:
			handler(query)
		elif handler:
			handler()
		else:
			self.send_error(404)

	def do_HEAD(self):
		req = Request(self.server.url, headers=self.server.cloudService.getHeaders())
		req.get_method = lambda: "HEAD"

		try:
			response = urlopen(req)
		except URLError as e:
			self.server.failed = True

			if e.code == 404:
				self.server.dialog.ok(self.server.settings.getLocalizedString(30003), self.server.settings.getLocalizedString(30209))
				return
			elif e.code == 401:
				self.server.dialog.ok(self.server.settings.getLocalizedString(30003), self.server.settings.getLocalizedString(30018))
				return
			elif e.code == 403 or e.code == 429:
				accountChange = False
				accounts = self.server.accountManager.getAccounts(self.server.driveID)

				for account in accounts[1:]:
					self.server.cloudService.setAccount(account)
					tokenRefresh = self.server.cloudService.refreshToken()

					if not tokenRefresh:
						continue

					if self.server.transcoded:
						self.server.url = self.server.cloudService.getStreams(self.server.fileID, (self.server.transcoded,))[1]

					req = Request(self.server.url, headers=self.server.cloudService.getHeaders())
					req.get_method = lambda: "HEAD"

					try:
						response = urlopen(req)
					except URLError:
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
		self.handleResponse(200, {
			"Content-Length": response.info().get("Content-Length"),
			"Content-Type": response.info().get("Content-Type"),
			"Cache-Control": response.info().get("Cache-Control"),
			"Date": response.info().get("Date"),
			"Accept-Ranges": "bytes",
		})
		response.close()
		self.server.length = response.info().get("Content-Length")

	def do_POST(self):
		pathHandlers = {
			"/add_sync_task": self.handleAddSyncTask,
			"/delete_drive": self.handleDeleteDrive,
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

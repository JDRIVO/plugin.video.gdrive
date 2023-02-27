import re
import urllib
import datetime
from threading import Thread
from socketserver import ThreadingMixIn
from http.server import BaseHTTPRequestHandler, HTTPServer

import xbmc
import xbmcgui

from .. import sync
from .. import accounts
from .. import playback
from .. import encryption
from .. import google_api
from . import registration


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""

class MyHTTPServer(ThreadingMixIn, HTTPServer):

	def __init__(self, settings):
		self.settings = settings
		self.port = self.settings.getSettingInt("server_port", 8011)
		super().__init__(("", self.port), MyStreamer)

		self.monitor = xbmc.Monitor()
		self.accountManager = accounts.manager.AccountManager(self.settings)
		self.cloudService = google_api.drive.GoogleDrive()
		self.taskManager = sync.tasker.Tasker(self.settings, self.accountManager)
		self.taskManager.run()

	def run(self):

		try:
			self.serve_forever()
		except Exception:
			self.server_close()

	def startPlayer(self, dbID, dbType, widget, trackProgress):
		vPlayer = playback.player.Player(dbID, dbType, int(widget), int(trackProgress), self.settings)
		expiry = self.cloudService.account.expiry

		while not self.monitor.abortRequested() and not vPlayer.close:

			if datetime.datetime.now() >= expiry:

				self.cloudService.refreshToken()

				if self.transcoded:
					self.playbackURL = self.cloudService.getStreams(self.fileID, (self.transcoded,))[1]

				self.accountManager.saveAccounts()

			if self.monitor.waitForAbort(1):
				break

class MyStreamer(BaseHTTPRequestHandler):

	def do_POST(self):

		if self.path == "/play_url":
			self.server.failed = False
			contentLength = int(self.headers["Content-Length"]) # <--- Gets the size of data
			postData = self.rfile.read(contentLength).decode("utf-8") # <--- Gets the data itself
			encrypted, self.server.playbackURL, self.server.driveID, fileID, transcoded = re.findall("encrypted=(.*)&url=(.*)&driveid=(.*)&fileid=(.*)&transcoded=(.*)", postData)[0]
			self.server.accountManager.loadAccounts()
			account = self.server.accountManager.getAccount(self.server.driveID)
			self.server.cloudService.setAccount(account)

			if encrypted == "True":
				self.server.crypto = True
			else:
				self.server.crypto = False

			if transcoded == "False":
				self.server.transcoded = False
			else:
				self.server.transcoded = transcoded
				self.server.fileID = fileID

			self.send_response(200)
			self.end_headers()

		elif self.path == "/start_player":
			contentLength = int(self.headers["Content-Length"])
			postData = self.rfile.read(contentLength).decode("utf-8")
			self.send_response(200)

			self.end_headers()
			dbID, dbType, widget, trackProgress = re.findall("dbid=([\d]+)&dbtype=(.*)&widget=(\d)&track=(\d)", postData)[0]
			Thread(target=self.server.startPlayer, args=(dbID, dbType, widget, trackProgress)).start()

		elif self.path == "/add_sync_task":
			contentLength = int(self.headers["Content-Length"])
			postData = self.rfile.read(contentLength).decode("utf-8")
			self.send_response(200)
			self.end_headers()
			driveID, folderID, folderName = re.findall("drive_id=(.*)&folder_id=(.*)&folder_name=(.*)", postData)[0]
			self.server.taskManager.createTask(driveID, folderID, folderName)

		elif self.path == "/register":
			contentLength = int(self.headers["Content-Length"]) # <--- Gets the size of data
			postData = self.rfile.read(contentLength).decode("utf-8") # <--- Gets the data itself

			accountName, clientID, clientSecret = re.findall("account=(.*)&client_id=(.*)&client_secret=(.*)", postData)[0]
			authURL = self.server.cloudService.getAuthURL(clientID, self.server.port)
			self.server.account = accounts.account.Account()
			self.server.account.name = urllib.parse.unquote_plus(accountName)
			self.server.account.clientID = clientID
			self.server.account.clientSecret = clientSecret

			self.send_response(303)
			self.send_header('Location', authURL)
			self.end_headers()

	def do_HEAD(self):

		if self.path == "/play":
			url = self.server.playbackURL
			req = urllib.request.Request(url, headers=self.server.cloudService.getHeaders())
			req.get_method = lambda: "HEAD"

			try:
				response = urllib.request.urlopen(req)
			except urllib.error.URLError as e:
				self.server.failed = True

				if e.code == 404:
					xbmcgui.Dialog().ok(self.server.settings.getLocalizedString(30003), self.server.settings.getLocalizedString(30209))
					return

				elif e.code == 401:
					xbmcgui.Dialog().ok(self.server.settings.getLocalizedString(30003), self.server.settings.getLocalizedString(30018))
					return

				elif e.code == 403 or e.code == 429:
					accountChange = False
					accounts = self.server.accountManager.getAccounts(self.server.driveID)

					for account in accounts:
						self.server.cloudService.setAccount(account)
						refreshToken = self.server.cloudService.refreshToken()

						if refreshToken == "failed":
							continue

						req = urllib.request.Request(url, headers=self.server.cloudService.getHeaders())
						req.get_method = lambda: "HEAD"

						try:
							response = urllib.request.urlopen(req)
						except urllib.error.URLError as e:
							continue

						accountChange = True
						xbmcgui.Dialog().notification(
							f"{self.server.settings.getLocalizedString(30003)}: {self.server.settings.getLocalizedString(30006)}",
							self.server.settings.getLocalizedString(30007),
						)
						break

					if not accountChange:
						xbmcgui.Dialog().ok(
							f"{self.server.settings.getLocalizedString(30003)}: {self.server.settings.getLocalizedString(30006)}",
							self.server.settings.getLocalizedString(30009),
						)
						return
					else:
						accounts.remove(account)
						accounts.insert(0, account)
						self.server.accountManager.saveAccounts()

				else:
					xbmc.log("gdrive error: " + str(e))
					return

			self.server.failed = False
			self.send_response(200)

			self.send_header("Content-Type", response.info().get("Content-Type"))
			self.send_header("Content-Length", response.info().get("Content-Length"))
			self.send_header("Cache-Control", response.info().get("Cache-Control"))
			self.send_header("Date", response.info().get("Date"))
			self.send_header("Content-type", "video/mp4")
			self.send_header("Accept-Ranges", "bytes")
			# self.send_header("ETag", response.info().get("ETag"))
			# self.send_header("Server", response.info().get("Server"))

			self.end_headers()
			# may want to add more granular control over chunk fetches
			# self.wfile.write(response.read())
			response.close()
			self.server.length = response.info().get("Content-Length")

	def do_GET(self):

		if self.path == "/play":

			if self.server.failed:
				return

			start, end = re.findall("([\d]+)-([\d]*)", self.headers["range"])[0]
			start = int(start) if start else ""
			end = int(end) if end else ""
			startOffset = 0

			if self.server.crypto and start != "" and start > 16 and end == "":
				# start = start - (16 - (end % 16))
				xbmc.log("START = " + str(start))
				startOffset = 16 - ((int(self.server.length) - start) % 16) + 8

			# if start == 23474184:
				# start = start - (16 - (end % 16))
				# start = 23474184 - 8

			url = self.server.playbackURL
			xbmc.log("GET " + url + "\n" + self.server.cloudService.getHeadersEncoded() + "\n")

			if start == "":
				req = urllib.request.Request(url, headers=self.server.cloudService.getHeaders())
			else:
				req = urllib.request.Request(
					url,
					headers=self.server.cloudService.getHeaders(
						additionalHeader="Range",
						additionalValue=f"bytes={start - startOffset}-{end}",
					)
				)

			try:
				response = urllib.request.urlopen(req)
			except urllib.error.URLError as e:
				xbmc.log("gdrive error: " + str(e))
				return

			if start == "":
				self.send_response(200)
				self.send_header("Content-Length", response.info().get("Content-Length"))
			else:
				self.send_response(206)
				self.send_header("Content-Length", str(int(response.info().get("Content-Length")) - startOffset))
				# self.send_header("Content-Range", "bytes " + str(start) + "-" + str(end))

				if not end:
					self.send_header("Content-Range", f"bytes {start}-{int(self.server.length) - 1}/{self.server.length}")
				else:
					self.send_header("Content-Range", f"bytes {start}-{end}/{self.server.length}")

				# self.send_header("Content-Range", response.info().get("Content-Range"))
				xbmc.log(f"Content-Range!!!{start}-{int(self.server.length) - 1}/{self.server.length}\n")

			xbmc.log(str(response.info()) + "\n")

			self.send_header("Content-Type", response.info().get("Content-Type"))
			# self.send_header("Content-Length", response.info().get("Content-Length"))
			self.send_header("Cache-Control", response.info().get("Cache-Control"))
			self.send_header("Date", response.info().get("Date"))
			self.send_header("Content-type", "video/mp4")
			self.send_header("Accept-Ranges", "bytes")

			self.end_headers()
			# may want to add more granular control over chunk fetches
			# self.wfile.write(response.read())

			if self.server.crypto:
				decrypt = encryption.encrypter.Encrypter(self.server.settings.getSetting("crypto_salt"), self.server.settings.getSetting("crypto_password"))

				try:
					decrypt.decryptStreamChunkOld(response, self.wfile, startOffset=startOffset)
				except Exception as e:
					xbmc.log(str(e))

			else:
				CHUNK = 16 * 1024

				try:

					while True:
						chunk = response.read(CHUNK)

						if not chunk:
							break

						self.wfile.write(chunk)

				except Exception as e:
					xbmc.log(str(e))

			response.close()

		elif self.path == "/register":
			self.send_response(200)
			self.end_headers()
			data = registration.form
			self.wfile.write(data.encode("utf-8"))

		elif "/status" in self.path:

			try:
				code = re.findall("code=(.*)&", self.path)[0]
				token = self.server.cloudService.getToken(self.server.account.clientID, self.server.account.clientSecret, code, self.server.port)
				self.server.account.accessToken = token["access_token"]
				self.server.account.refreshToken = token["refresh_token"]
				self.server.cloudService.setAccount(self.server.account)
				self.server.cloudService.refreshToken()
				driveID = self.server.cloudService.getDriveID()
				self.server.accountManager.loadAccounts()
				self.server.accountManager.addAccount(
					self.server.account,
					driveID,
				)
				redirect = "/registration_succeeded"
			except Exception as e:
				redirect = "/registration_failed"

			self.send_response(303)
			self.send_header('Location', f"http://localhost:{self.server.port}redirect")
			self.end_headers()

		elif self.path == "/registration_succeeded":
			self.send_response(200)
			self.end_headers()
			data = registration.status("Account registration succeeded")
			self.wfile.write(data.encode("utf-8"))

		elif self.path == "/registration_failed":
			self.send_response(200)
			self.end_headers()
			data = registration.status("Account registration failed")
			self.wfile.write(data.encode("utf-8"))

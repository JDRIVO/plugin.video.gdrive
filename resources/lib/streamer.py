"""
	Copyright (C) 2014-2016 ddurdle

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""

import re
import sys
import time
import urllib
import xbmc
import xbmcgui
import constants
from threading import Thread
from socketserver import ThreadingMixIn
from http.server import BaseHTTPRequestHandler, HTTPServer
from resources.lib import encryption, enrolment, gplayer


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""


class MyHTTPServer(ThreadingMixIn, HTTPServer):

	def __init__(self, *args, **kwargs):
		HTTPServer.__init__(self, *args, **kwargs)
		self.ready = True
		self.close = False

	def run(self):

		try:
			self.serve_forever()
		except:
			self.close = True
			# Clean-up server (close socket, etc.)
			self.server_close()

	def setDetails(self, PLUGIN_HANDLE, PLUGIN_NAME, PLUGIN_URL, addon, userAgent, settings):
		self.PLUGIN_HANDLE = PLUGIN_HANDLE
		self.PLUGIN_NAME = PLUGIN_NAME
		self.PLUGIN_URL = PLUGIN_URL
		self.addon = addon
		self.userAgent = userAgent
		self.settings = settings
		# self.domain = domain
		self.playbackURL = ""
		self.crypto = False
		self.ready = True

	def startGPlayer(self, dbID, dbType, widget, trackProgress):
		lastUpdate = time.time()
		player = gplayer.GPlayer(dbID=dbID, dbType=dbType, widget=int(widget), trackProgress=int(trackProgress))

		while not player.close and not self.close:

			if time.time() - lastUpdate >= 1740:
				lastUpdate = time.time()
				self.service.refreshToken()

			xbmc.sleep(1000)

class MyStreamer(BaseHTTPRequestHandler):

	# Handler for the GET requests
	def do_POST(self):
		# debug - print headers in log
		headers = str(self.headers)
		print(headers)

		# passed a kill signal?
		if self.path == "/kill":
			self.server.ready = False
			return

		elif self.path == "/crypto_playurl":
			contentLength = int(self.headers["Content-Length"]) # <--- Gets the size of data
			postData = self.rfile.read(contentLength).decode("utf-8") # <--- Gets the data itself

			for r in re.finditer("instance\=([^\&]+)\&url\=([^\|]+)", postData, re.DOTALL):
				instanceName = r.group(1)
				url = r.group(2)
				driveStream = ""
				xbmc.log("drive_stream = " + driveStream + "\n")
				xbmc.log("url = " + url + "\n")
				cloudservice2 = constants.cloudservice2
				self.server.service = cloudservice2(
					self.server.PLUGIN_HANDLE,
					self.server.PLUGIN_URL,
					self.server.addon,
					instanceName,
					self.server.userAgent,
					self.server.settings,
				)
				self.server.crypto = True
				self.server.playbackURL = url
				self.server.driveStream = driveStream

			self.server.service.refreshToken()
			self.send_response(200)
			self.end_headers()

		elif self.path == "/start_gplayer":
			contentLength = int(self.headers["Content-Length"])
			postData = self.rfile.read(contentLength).decode("utf-8")
			self.send_response(200)
			self.end_headers()

			for r in re.finditer("dbid\=([^\&]+)\&dbtype\=([^\|]+)\&widget\=([^\|]+)\&track\=([^\|]+)", postData, re.DOTALL):
				dbID = r.group(1)
				dbType = r.group(2)
				widget = r.group(3)
				trackProgress = r.group(4)

			Thread(target=self.server.startGPlayer, args=(dbID, dbType, widget, trackProgress)).start()

		# redirect url to output
		elif self.path == "/enroll?default=false":
			contentLength = int(self.headers["Content-Length"])  # <--- Gets the size of data
			postData = self.rfile.read(contentLength).decode("utf-8")  # <--- Gets the data itself
			self.send_response(200)
			self.end_headers()

			for r in re.finditer("client_id=([^&]+)&client_secret=([^&]+)", postData, re.DOTALL):
				clientID = r.group(1)
				clientSecret = r.group(2)
				data = enrolment.page2(clientID, clientSecret)
				self.wfile.write(data.encode("utf-8"))

		# redirect url to output
		elif self.path == "/enroll":
			contentLength = int(self.headers["Content-Length"])  # <--- Gets the size of data
			postData = self.rfile.read(contentLength).decode("utf-8")  # <--- Gets the data itself
			self.send_response(200)
			self.end_headers()

			for r in re.finditer("account=([^&]+)&code=([^&]+)&client_id=([^&]+)&client_secret=([^&]+)", postData, re.DOTALL):
				account = r.group(1)
				clientID = r.group(3)
				clientSecret = r.group(4)
				code = r.group(2)
				code = code.replace("%2F", "/")

				count = 1

				while True:
					instanceName = self.server.PLUGIN_NAME + str(count)

					try:
						username = self.server.settings.getSetting(instanceName + "_username")
					except:
						username = ""

					if username == account or username == "":
						self.server.addon.setSetting(instanceName + "_username", str(account))
						self.server.addon.setSetting(instanceName + "_code", str(code))
						self.server.addon.setSetting(instanceName + "_client_id", str(clientID))
						self.server.addon.setSetting(instanceName + "_client_secret", str(clientSecret))

						if count > self.server.addon.getSettingInt("account_amount"):
							self.server.addon.setSetting("account_amount", str(count))

						break

					count += 1

				url = "https://accounts.google.com/o/oauth2/token"
				header = {"User-Agent": self.server.userAgent, "Content-Type": "application/x-www-form-urlencoded"}
				url = "https://accounts.google.com/o/oauth2/token"
				data = "code={}&client_id={}&client_secret={}&redirect_uri=urn:ietf:wg:oauth:2.0:oob&grant_type=authorization_code".format(
					code, clientID, clientSecret
				)
				req = urllib.request.Request(url, data.encode("utf-8"), header)

				# try login
				try:
					response = urllib.request.urlopen(req)
				except urllib.error.URLError as e:
					self.send_response(200)
					self.end_headers()
					self.wfile.write(str(e).encode("utf-8"))
					return

				responseData = response.read().decode("utf-8")
				response.close()

				# retrieve authorization token
				for r in re.finditer('\"access_token\"\s?\:\s?\"([^\"]+)\".+?' + '\"refresh_token\"\s?\:\s?\"([^\"]+)\".+?', responseData, re.DOTALL):
					accessToken, refreshToken = r.groups()
					self.server.addon.setSetting(instanceName + "_auth_access_token", str(accessToken))
					self.server.addon.setSetting(instanceName + "_auth_refresh_token", str(refreshToken))
					self.wfile.write(b"Successfully enrolled account.")
					self.server.ready = False

				for r in re.finditer('\"error_description\"\s?\:\s?\"([^\"]+)\"', responseData, re.DOTALL):
					errorMessage = r.group(1)
					self.wfile.write(errorMessage.encode("utf-8"))

				return

	def do_HEAD(self):
		# debug - print headers in log
		headers = str(self.headers)
		print(headers)

		# passed a kill signal?
		if self.path == "/kill":
			self.server.ready = False
			return

		# redirect url to output
		elif self.path == "/play":
			url = self.server.playbackURL
			xbmc.log("HEAD " + url + "\n")
			req = urllib.request.Request(url, None, self.server.service.getHeadersList())
			req.get_method = lambda: "HEAD"

			try:
				response = urllib.request.urlopen(req)
			except urllib.error.URLError as e:

				if e.code == 404:
					xbmcgui.Dialog().ok(self.server.addon.getLocalizedString(30003), self.server.addon.getLocalizedString(30209))
					return
				elif e.code == 401:
					xbmc.log("ERROR\n" + self.server.service.getHeadersEncoded())
					xbmcgui.Dialog().ok(self.server.addon.getLocalizedString(30003), self.server.addon.getLocalizedString(30018))
					return
				elif e.code == 403 or e.code == 429:
					xbmc.log("ERROR\n" + self.server.service.getHeadersEncoded())

					if not self.server.addon.getSetting("fallback"):
						xbmcgui.Dialog().ok(
							self.server.addon.getLocalizedString(30003) + ": " + self.server.addon.getLocalizedString(30006),
							self.server.addon.getLocalizedString(30009),
						)
						return

					fallbackAccounts = self.server.addon.getSetting("fallback_accounts").split(",")
					defaultAccount = self.server.addon.getSetting("default_account")
					accountChange = False

					for fallbackAccount in fallbackAccounts:
						username = self.server.addon.getSetting("gdrive{}_username".format(fallbackAccount))

						if not username:
							fallbackAccounts.remove(fallbackAccount)
							continue

						try:
							cloudservice2 = constants.cloudservice2
							self.server.service = cloudservice2(
								self.server.PLUGIN_HANDLE,
								self.server.PLUGIN_URL,
								self.server.addon,
								"gdrive" + fallbackAccount,
								self.server.userAgent,
								self.server.settings,
							)
							self.server.service.refreshToken()

							req = urllib.request.Request(url, None, self.server.service.getHeadersList())
							req.get_method = lambda: "HEAD"
							response = urllib.request.urlopen(req)

							if not defaultAccount in fallbackAccounts:
								fallbackAccounts.append(defaultAccount)

							fallbackAccounts.remove(fallbackAccount)
							self.server.addon.setSetting("default_account", fallbackAccount)
							self.server.addon.setSetting("default_account_ui", username)
							accountChange = True
							xbmcgui.Dialog().notification(
								self.server.addon.getLocalizedString(30003) + ": " + self.server.addon.getLocalizedString(30006),
								self.server.addon.getLocalizedString(30007),
							)
							break

						except:
							continue

					self.server.addon.setSetting("fallback_accounts", ",".join(fallbackAccounts))
					self.server.addon.setSetting(
						"fallback_accounts_ui",
						", ".join(
							self.server.addon.getSetting("gdrive{}_username".format(x))
							for x in fallbackAccounts
						)
					)

					if not accountChange:
						xbmcgui.Dialog().ok(
							self.server.addon.getLocalizedString(30003) + ": " + self.server.addon.getLocalizedString(30006),
							self.server.addon.getLocalizedString(30009),
						)
						return

				else:
					return

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

			## may want to add more granular control over chunk fetches
			# self.wfile.write(response.read())

			response.close()
			xbmc.log("DONE")
			self.server.length = response.info().get("Content-Length")

	# Handler for the GET requests
	def do_GET(self):
		# debug - print headers in log
		headers = str(self.headers)
		print(headers)

		start = end = ""
		startOffset = 0

		for r in re.finditer("Range\:\s+bytes\=(\d+)\-", headers, re.DOTALL):
			start = int(r.group(1))
			break

		for r in re.finditer("Range\:\s+bytes\=\d+\-(\d+)", headers, re.DOTALL):
			end = int(r.group(1))
			break

		# passed a kill signal?
		if self.path == "/kill":
			self.server.ready = False
			return

		# redirect url to output
		elif self.path == "/play":

			if self.server.crypto and start != "" and start > 16 and end == "":
				# start = start - (16 - (end % 16))
				xbmc.log("START = " + str(start))
				startOffset = 16 - ((int(self.server.length) - start) % 16) + 8

			# if (self.server.crypto and start == 23474184):
				# start = start - (16 - (end % 16))
				# start = 23474184 - 8

			url = self.server.playbackURL
			xbmc.log("GET " + url + "\n" + self.server.service.getHeadersEncoded() + "\n")

			if start == "":
				req = urllib.request.Request(url, None, self.server.service.getHeadersList())
			else:
				req = urllib.request.Request(
					url,
					None,
					self.server.service.getHeadersList(
						additionalHeader="Range",
						additionalValue="bytes=" + str(start - startOffset) + "-" + str(end),
					)
				)

			try:
				response = urllib.request.urlopen(req)
			except urllib.error.URLError as e:

				if e.code == 403 or e.code == 401:
					xbmc.log("ERROR\n" + self.server.service.getHeadersEncoded())
					self.server.service.refreshToken()
					req = urllib.request.Request(url, None, self.server.service.getHeadersList())

					try:
						response = urllib.request.urlopen(req)
					except:
						xbmc.log("STILL ERROR\n" + self.server.service.getHeadersEncoded())
						return

				else:
					return

			if start == "":
				self.send_response(200)
				self.send_header("Content-Length", response.info().get("Content-Length"))
			else:
				self.send_response(206)
				self.send_header("Content-Length", str(int(response.info().get("Content-Length")) - startOffset))
				# self.send_header("Content-Range", "bytes " + str(start) + "-" + str(end))

				if end == "":
					self.send_header("Content-Range", "bytes {}-{}/{}".format(start, int(self.server.length) - 1, self.server.length))
				else:
					self.send_header("Content-Range", "bytes {}-{}/{}".format(start, end, self.server.length))

				# self.send_header("Content-Range", response.info().get("Content-Range"))
				xbmc.log("Content-Range!!!{}-{}/{}\n".format(start, int(self.server.length) - 1, self.server.length))

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
				decrypt = encryption.Encryption(self.server.addon.getSetting("crypto_salt"), self.server.addon.getSetting("crypto_password"))
				CHUNK = 16 * 1024
				decrypt.decryptStreamChunkOld(response, self.wfile, startOffset=startOffset)

			response.close()

		# redirect url to output
		elif self.path == "/enroll":
			self.send_response(200)
			self.end_headers()
			self.wfile.write(enrolment.page1)
			return

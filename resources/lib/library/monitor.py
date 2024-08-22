import os
import json

import xbmc

import constants
from . import editor


class LibraryMonitor(xbmc.Monitor):

	def __init__(self):
		self.settings = constants.settings
		self.dbEditor = editor.DatabaseEditor()
		self.enabled = self.isEnabled()

	@staticmethod
	def jsonQuery(query):
		query = json.dumps(query)
		return json.loads(xbmc.executeJSONRPC(query))

	def onNotification(self, sender, method, data):

		if method != "VideoLibrary.OnUpdate" or not self.enabled:
			return

		data = json.loads(data)

		if "item" in data and "type" in data.get("item") and data.get("item").get("type") in ("episode", "movie"):
			dbID = data["item"]["id"]
			dbType = data["item"]["type"]

			if dbType == "movie":
				query =	{
					"jsonrpc": "2.0",
					"id": "1",
					"method": "VideoLibrary.GetMovieDetails",
					"params": {"movieid": dbID, "properties": ["file"]},
				}
				jsonKey = "moviedetails"
			else:
				query = {
					"jsonrpc": "2.0",
					"id": "1",
					"method": "VideoLibrary.GetEpisodeDetails",
					"params": {"episodeid": dbID, "properties": ["file"]},
				}
				jsonKey = "episodedetails"

			jsonResponse = self.jsonQuery(query)
			filePath = jsonResponse["result"][jsonKey]["file"]
			dirPath = os.path.dirname(filePath)
			filename = os.path.basename(filePath)
			fileExtension = os.path.splitext(filename)[1]

			if fileExtension == ".strm":
				self.dbEditor.processData(filePath, dirPath, filename)

	def onSettingsChanged(self):
		self.enabled = self.isEnabled()

	def isEnabled(self):
		return self.settings.getSetting("library_monitor")

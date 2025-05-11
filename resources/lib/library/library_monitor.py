import os
import json

import xbmc

from constants import SETTINGS
from helpers import rpc
from .library_editor import DatabaseEditor


class LibraryMonitor(xbmc.Monitor):

	def __init__(self):
		self.settings = SETTINGS
		self.dbEditor = DatabaseEditor()
		self.enabled = self._isEnabled()

	def onNotification(self, sender, method, data):

		if method != "VideoLibrary.OnUpdate" or not self.enabled:
			return

		data = json.loads(data)
		item = data.get("item")

		if not item:
			return

		type = item.get("type")

		if type in ("movie", "episode"):
			query = {
				"method": "VideoLibrary.GetMovieDetails" if type == "movie" else "VideoLibrary.GetEpisodeDetails",
				"params": {f"{type}id": item["id"], "properties": ["file"]},
			}
			response = rpc(query)
			filePath = response["result"][f"{type}details"]["file"]
			dirPath = os.path.dirname(filePath)
			filename = os.path.basename(filePath)
			fileExtension = os.path.splitext(filename)[1]

			if fileExtension == ".strm":
				self.dbEditor.processData(filePath, dirPath, filename)

	def onSettingsChanged(self):
		self.enabled = self._isEnabled()

	def _isEnabled(self):
		return self.settings.getSetting("library_monitor")

import os
import re
import json
from sqlite3 import dbapi2 as sqlite

import xbmc
import xbmcvfs

import constants
from . import helpers
from .. import filesystem
from ..database.database import Database


class LibraryMonitor(Database, xbmc.Monitor):

	def __init__(self):
		dbPath = helpers.getVideoDB()
		super().__init__(dbPath)
		self.settings = constants.settings
		self.getSettings()
		self.fileOperations = filesystem.operations.FileOperations()

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
			filename = os.path.basename(filePath)
			fileExt = os.path.splitext(filename)[1]

			if fileExt != ".strm":
				return

			fileDir = os.path.dirname(filePath) + os.sep
			strmData = self.fileOperations.readFile(filePath)

			try:
				fileID = self.selectConditional("files", "idFile", f'idPath=(SELECT idPath FROM path WHERE strPath="{fileDir}") AND strFilename="{filename}"')
			except Exception as e:
				xbmc.log(f"gdrive error: Monitor error {e}", xbmc.LOGERROR)
				return

			if not fileID:
				return

			mediaData = self.mediaDataConversion(strmData, fileID)

			for data in mediaData:

				if not data:
					continue

				type, values = data

				if type == "video" and self.selectAllConditional("streamdetails", f"idFile='{fileID}' AND iStreamType='0'"):
					self.update("streamdetails", values, f"idFile='{fileID}' AND iStreamType='0'")
				elif type == "audio" and self.selectAllConditional("streamdetails", f"idFile='{fileID}' AND iStreamType='1'"):
					self.update("streamdetails", values, f"idFile='{fileID}' AND iStreamType='1'")
				else:
					self.insert("streamdetails", values)

	def mediaDataConversion(self, strmData, fileID):
		videoData = {
			"video_codec": "strVideoCodec",
			"hdr": "strHdrType",
			"aspect_ratio": "fVideoAspect",
			"video_width": "iVideoWidth",
			"video_height": "iVideoHeight",
			"video_duration": "iVideoDuration",
		}
		audioData = {
			"audio_codec": "strAudioCodec",
			"audio_channels": "iAudioChannels",
		}
		strmData = self.settings.parseQuery(strmData)
		video = {videoData[k]: v for k, v in strmData.items() if videoData.get(k)}
		audio = {audioData[k]: v for k, v in strmData.items() if audioData.get(k)}

		if video:
			video.update({"idFile": fileID, "iStreamType": "0"})
			video = ["video", video]

		if audio:
			audio.update({"idFile": fileID, "iStreamType": "1"})
			audio = ["audio", audio]

		return video, audio

	def onSettingsChanged(self):
		self.getSettings()

	def getSettings(self):
		self.enabled = self.settings.getSetting("library_monitor")

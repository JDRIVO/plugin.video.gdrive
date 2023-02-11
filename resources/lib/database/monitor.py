import os
import re
import json
from sqlite3 import dbapi2 as sqlite

import xbmc
import xbmcvfs

import constants
from . import helpers
from .. import filesystem


class LibraryMonitor(xbmc.Monitor):

	def __init__(self):
		self.settings = constants.settings
		self.getSettings()
		self.fileOperations = filesystem.operations.FileOperations(None, None)

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
			fileName = os.path.basename(filePath)
			fileExt = os.path.splitext(fileName)[1]

			if fileExt != ".strm":
				return

			fileDir = os.path.dirname(filePath) + os.sep
			strmData = self.fileOperations.readFile(filePath)
			mediaInfo = self.mediaInfoConversion(strmData)

			if not mediaInfo:
				return

			try:
				fileID = self.select(
					(
						"SELECT idFile FROM files WHERE idPath=(SELECT idPath FROM path WHERE strPath=?) AND strFilename=?",
						(fileDir, fileName),
					),
				)
			except Exception:
				xbmc.log("gdrive error: Your video database is incompatible with this Kodi version")
				return

			self.insert(self.statementConstructor(mediaInfo, fileID))

	@staticmethod
	def mediaInfoConversion(strmData):
		videoInfo = {
			"video_codec": "strVideoCodec",
			"hdr": "strHdrType",
			"aspect_ratio": "fVideoAspect",
			"video_width": "iVideoWidth",
			"video_height": "iVideoHeight",
			"video_duration": "iVideoDuration",
		}
		audioInfo = {
			"audio_codec": "strAudioCodec",
			"audio_channels": "iAudioChannels",
		}
		videoNames, videoValues, audioNames, audioValues = [], [], [], []
		strmData = strmData.split("&")

		try:

			for params in strmData:
				name, value = params.split("=")

				if not value:
					continue

				if name in videoInfo:
					videoNames.append(videoInfo[name])
					videoValues.append(value)
				elif name in audioInfo:
					audioNames.append(audioInfo[name])
					audioValues.append(value)

		except Exception:
			return

		converted = []

		if videoNames:
			videoNames.append("iStreamType")
			videoValues.append("0")
			converted.append((videoNames, videoValues))

		if audioNames:
			audioNames.append("iStreamType")
			audioValues.append("1")
			converted.append((audioNames, audioValues))

		if converted:
			return converted

	@staticmethod
	def statementConstructor(mediaInfo, fileID):
		statements = []

		for names, values in mediaInfo:
			names.append("idFile")
			values.append(fileID)
			condition = "".join(
				[
					"{}='{}' AND ".format(name, values[count])
					if name != names[-1]
					else "{}='{}'".format(name, values[count])
					for count, name in enumerate(names)
				]
			)
			names = ", ".join(names)
			values = str(values)[1:-1]
			statements.append(
				"INSERT INTO streamdetails ({}) SELECT {} WHERE NOT EXISTS (SELECT 1 FROM streamdetails WHERE {})".format(
					names, values, condition
				)
			)

		return statements

	def select(self, statement):
		xbmc.log("the select statement = " + str(statement), xbmc.LOGERROR)
		db = sqlite.connect(self.dbPath)
		query = list(db.execute(*statement))
		db.close()
		return query[0][0]

	def insert(self, statements):
		xbmc.log("the insert statements = " + str(statements), xbmc.LOGERROR)
		db = sqlite.connect(self.dbPath)
		[db.execute(statement) for statement in statements]
		db.commit()
		db.close()

	def onSettingsChanged(self):
		self.getSettings()

	def getSettings(self):
		self.enabled = self.settings.getSetting("library_monitor")
		self.dbPath = helpers.getVideoDB()

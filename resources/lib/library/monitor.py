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
			except Exception as e:
				xbmc.log(f"gdrive error: Monitor error {e}", xbmc.LOGERROR)

			if not fileID:
				return

			fileID = fileID[0][0]
			self.insertMultiple(self.statementConstructor(mediaInfo, fileID))

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
					f"{name}='{values[count]}' AND "
					if name != names[-1]
					else f"{name}='{values[count]}'"
					for count, name in enumerate(names)
				]
			)
			names = ", ".join(names)
			values = str(values)[1:-1]
			statements.append(
				f"INSERT INTO streamdetails ({names}) SELECT {values} WHERE NOT EXISTS (SELECT 1 FROM streamdetails WHERE {condition})"
			)

		return statements

	def select(self, statement):
		db = sqlite.connect(self.dbPath)
		query = db.execute(*statement)
		query = query.fetchall()
		db.close()
		return query

	def insert(self, statement):
		db = sqlite.connect(self.dbPath)
		db.execute(statement)
		db.commit()
		db.close()

	def insertMultiple(self, statements):
		db = sqlite.connect(self.dbPath)
		[db.execute(statement) for statement in statements]
		db.commit()
		db.close()

	def onSettingsChanged(self):
		self.getSettings()

	def getSettings(self):
		self.enabled = self.settings.getSetting("library_monitor")
		self.dbPath = helpers.getVideoDB()

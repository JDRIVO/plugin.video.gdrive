import os
import json
import xbmc
import xbmcvfs
import constants
from sqlite3 import dbapi2 as sqlite


def run():
	monitor = xbmc.Monitor()
	watcher = LibraryMonitor()

	while not monitor.abortRequested() and watcher.enabled:

		if monitor.waitForAbort(1):
			break


class LibraryMonitor(xbmc.Monitor):

	def __init__(self):
		self.settings = constants.addon
		self.getSettings()

	def openFile(self, path):

		with open(path, "rb") as strm:
			return strm.read().decode("utf-8")

	def jsonQuery(self, query):
		query = json.dumps(query)
		result = xbmc.executeJSONRPC(query)
		return json.loads(result)

	def onNotification(self, sender, method, data):

		if method == "VideoLibrary.OnUpdate":
			response = json.loads(data)

			if "item" in response and "type" in response.get("item") and response.get("item").get("type") in ("episode", "movie"):
				dbID = response["item"]["id"]
				dbType = response["item"]["type"]

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

				strmPath = jsonResponse["result"][jsonKey]["file"]
				strmName = os.path.basename(strmPath)
				strmDir = os.path.dirname(strmPath) + os.sep
				strmData = self.openFile(strmPath)

				mediaInfo = self.mediaInfoConversion(strmData)

				if not mediaInfo:
					return

				try:
					fileID = self.select(
						(
							"SELECT idFile FROM files WHERE idPath=(SELECT idPath FROM path WHERE strPath=?) AND strFilename=?",
							(strmDir, strmName),
						),
					)
				except:
					xbmc.log(
						self.settings.getLocalizedString(30003) + ": " + self.settings.getLocalizedString(30221),
						xbmc.LOGERROR,
					)
					return

				statement = self.statementConstructor(mediaInfo, fileID)
				self.insert(statement)

	@staticmethod
	def mediaInfoConversion(strmData):
		# "Apollo 13 (1995) Anniversary Edition&aspect_ratio=33&audio_codec=69"

		videoInfo = {
			"video_codec": "strVideoCodec",
			"aspect_ratio": "fVideoAspect",
			"video_width": "iVideoWidth",
			"video_height": "iVideoHeight",
			"video_duration": "iVideoDuration"
		}
		audioInfo = {
			"audio_codec": "strAudioCodec",
			"audio_channels": "iAudioChannels"
		}

		videoNames, videoValues, audioNames, audioValues = [], [], [], []
		strmData = strmData.split("&")

		for params in strmData:
			params = params.split("=")
			mediaInfo = params[0]
			match = False

			if mediaInfo in videoInfo:
				match = True
				names = videoNames
				values = videoValues
				media = videoInfo
			elif mediaInfo in audioInfo:
				match = True
				names = audioNames
				values = audioValues
				media = audioInfo

			if match:
				value = params[1]

				if value:
					names.append(media[mediaInfo])
					values.append(value)

		converted = {}

		if videoNames:
			videoNames.append("iStreamType")
			videoValues.append("0")
			converted["video"] = videoNames, videoValues

		if audioNames:
			audioNames.append("iStreamType")
			audioValues.append("1")
			converted["audio"] = audioNames, audioValues

		if converted:
			return converted

	@staticmethod
	def statementConstructor(mediaInfo, fileID):
		statements = []

		for k, v in mediaInfo.items():
			v[0].append("idFile")
			v[1].append(str(fileID))
			reconstruct = "".join(
				[
					"{}='{}' AND ".format(value, v[1][count])
					if value != v[0][-1]
					else "{}='{}'".format(value, v[1][count])
					for count, value in enumerate(v[0])
				]
			)
			rows, values = ", ".join(v[0]), str(v[1])[1:-1]
			statements.append(
				"INSERT INTO streamdetails ({}) SELECT {} WHERE NOT EXISTS (SELECT 1 FROM streamdetails WHERE {})".format(
					rows, values, reconstruct
				)
			)

		return statements

	def select(self, statement):
		db = sqlite.connect(self.dbPath)
		query = list(db.execute(*statement))
		db.close()
		return query[0][0]

	def insert(self, statements):
		db = sqlite.connect(self.dbPath)

		for statement in statements:
			db.execute(statement)

		db.commit()
		db.close()

	def onSettingsChanged(self):
		self.getSettings()

	def getSettings(self):
		self.enabled = self.settings.getSetting("watcher")
		self.dbPath = xbmcvfs.translatePath(self.settings.getSetting("video_db"))

	# strVideoCodec, iVideoWidth, iVideoHeight, fVideoAspect, iStreamType, idFile
	# 'h264', '1920', '1080', '1.77777777778', '0', '70'
	# strVideoCodec='h264' AND iVideoWidth='1920' AND iVideoHeight='1080' AND fVideoAspect='1.77777777778' AND iStreamType='0' AND idFile='70'
	# cursor = db.execute("INSERT INTO streamdetails (strVideoCodec, strAudioCodec) SELECT 'test1', 'test2' EXCEPT SELECT strVideoCodec, strAudioCodec FROM streamdetails WHERE strVideoCodec='test1' AND strAudioCodec='test2'")
	# cursor = db.execute("INSERT INTO streamdetails (strVideoCodec, strAudioCodec) SELECT 'test1', 'test2' WHERE NOT EXISTS (SELECT strVideoCodec, strAudioCodec FROM streamdetails WHERE strVideoCodec='test1' AND strAudioCodec='test2')")

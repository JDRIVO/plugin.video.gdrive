import os

import xbmcvfs

import constants
from .. import filesystem
from ..database.database import Database


class DatabaseEditor(Database):

	def __init__(self):
		super().__init__(self._getVideoDB())
		self.settings = constants.settings
		self.fileOperations = filesystem.operations.FileOperations()

	def processData(self, strmPath, dirPath, filename):
		strmData = self.settings.parseQuery(self.fileOperations.readFile(strmPath))

		if not strmData or "plugin://plugin.video.gdrive/?mode" not in strmData:
			return

		fileID = self._getFileID(dirPath, filename)

		if not fileID:
			return

		videoData = self._extractStreamData(fileID, strmData, "video")
		audioData = self._extractStreamData(fileID, strmData, "audio")

		if videoData:
			self._addStreamData(fileID, videoData, "video")

		if audioData:
			self._addStreamData(fileID, audioData, "audio")

	def _addStreamData(self, fileID, data, mediaType):
		streamType = "0" if mediaType == "video" else "1"

		if self.selectAll("streamdetails", {"idFile": fileID, "iStreamType": streamType}):
			self.update("streamdetails", data, {"idFile": fileID, "iStreamType": streamType})
		else:
			self.insert("streamdetails", data)

	def _extractStreamData(self, fileID, data, mediaType):

		if mediaType == "video":
			streamType = "0"
			values = {
				"video_width": "iVideoWidth",
				"video_height": "iVideoHeight",
				"aspect_ratio": "fVideoAspect",
				"video_duration": "iVideoDuration",
				"video_codec": "strVideoCodec",
				"hdr": "strHdrType",
			}
		else:
			streamType = "1"
			values = {
				"audio_codec": "strAudioCodec",
				"audio_channels": "iAudioChannels",
			}

		data = {values[k]: v for k, v in data.items() if k in values}

		if data:
			data.update({"idFile": fileID, "iStreamType": streamType})

		return data

	def _getFileID(self, dirPath, filename):
		return self.select("files", "idFile", {"idPath": f'(SELECT idPath FROM path WHERE strPath="{dirPath + os.sep}")', "strFilename": filename})

	def _getVideoDB(self):
		dbDirectory = xbmcvfs.translatePath("special://database")
		directories = os.listdir(dbDirectory)
		videoDatabase = [dir for dir in directories if "MyVideos" in dir][0]
		return os.path.join(dbDirectory, videoDatabase)

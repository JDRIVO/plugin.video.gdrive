import os

import xbmcvfs

import constants
from .. import filesystem
from ..database.database import Database


class DatabaseEditor(Database):

	def __init__(self):
		super().__init__(self.getVideoDB())
		self.settings = constants.settings
		self.fileOperations = filesystem.operations.FileOperations()

	def getVideoDB(self):
		dbDirectory = xbmcvfs.translatePath("special://database")
		directories = os.listdir(dbDirectory)
		videoDatabase = [dir for dir in directories if "MyVideos" in dir][0]
		return os.path.join(dbDirectory, videoDatabase)

	def processData(self, strmPath, dirPath, filename):
		strmData = self.fileOperations.readFile(strmPath)
		fileID = self.getFileID(dirPath, filename)

		if not fileID:
			return

		videoData = self.extractMediaData(fileID, strmData, "video")
		audioData = self.extractMediaData(fileID, strmData, "audio")

		if videoData:
			self.addMediaData(fileID, videoData, "video")

		if audioData:
			self.addMediaData(fileID, audioData, "audio")

	def extractMediaData(self, fileID, data, mediaType):

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

		data = self.settings.parseQuery(data)
		data = {values[k]: v for k, v in data.items() if k in values}

		if data:
			data.update({"idFile": fileID, "iStreamType": streamType})

		return data

	def addMediaData(self, fileID, data, mediaType):

		if mediaType == "video":
			streamType = "0"
		else:
			streamType = "1"

		if self.selectAll("streamdetails", {"idFile": fileID, "iStreamType": streamType}):
			self.update("streamdetails", data, {"idFile": fileID, "iStreamType": streamType})
		else:
			self.insert("streamdetails", data)

	def getFileID(self, dirPath, filename):
		return self.select("files", "idFile", {"idPath": f'(SELECT idPath FROM path WHERE strPath="{dirPath + os.sep}")', "strFilename": filename})

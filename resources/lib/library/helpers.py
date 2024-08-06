import os

import xbmcvfs

from ..database.database import Database


def getVideoDB():
	dbDirectory = xbmcvfs.translatePath("special://database")
	directories = os.listdir(dbDirectory)
	videoDatabase = [dir for dir in directories if "MyVideos" in dir][0]
	return os.path.join(dbDirectory, videoDatabase)

def updateLibrary(filePath, metadata):
	dirPath, filename = os.path.split(filePath)
	dbPath = getVideoDB()
	db = Database(dbPath)
	fileID = db.selectConditional("files", "idFile", {"idPath": f'(SELECT idPath FROM path WHERE strPath="{dirPath + os.sep}")', "strFilename": filename})

	if not fileID:
		return

	data = {
		"fVideoAspect": float(metadata["width"]) / metadata["height"],
		"iVideoWidth": metadata["width"],
		"iVideoHeight": metadata["height"],
		"iVideoDuration": float(metadata["durationMillis"]) / 1000,
	}
	condition = {"idFile": fileID, "iStreamType": "0"}

	if db.selectAllConditional("streamdetails", condition):
		db.update("streamdetails", data, condition)
	else:
		db.insert("streamdetails", data)

import os
import re

import xbmc
import xbmcvfs

from ..database.database import Database


def getVideoDB():
	dbVersion = {
		"19": "119",
		"20": "121",
		"21": "131",
	}
	userAgent = xbmc.getUserAgent()
	kodiVersion = re.findall("Kodi\/(\d+)", userAgent)[0]
	return os.path.join(xbmcvfs.translatePath("special://database"), f"MyVideos{dbVersion[kodiVersion]}.db")

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

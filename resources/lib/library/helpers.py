import os
import re

import xbmc
import xbmcvfs

from ..database.database import Database


def getVideoDB():
	dbVersion = {
		"19": "119",
		"20": "121",
	}
	userAgent = xbmc.getUserAgent()
	kodiVersion = re.findall("Kodi\/(\d+)", userAgent)[0]
	return os.path.join(xbmcvfs.translatePath("special://database"), f"MyVideos{dbVersion[kodiVersion]}.db")

def updateLibrary(filePath, metadata):
	dirPath, filename = os.path.split(filePath)
	dbPath = getVideoDB()
	db = Database(dbPath)
	fileID = db.selectConditional("files", "idFile", f'idPath=(SELECT idPath FROM path WHERE strPath="{dirPath + os.sep}") AND strFilename="{filename}"')

	if not fileID:
		return

	data = {
		"fVideoAspect": float(metadata["width"]) / metadata["height"],
		"iVideoWidth": metadata["width"],
		"iVideoHeight": metadata["height"],
		"iVideoDuration": float(metadata["durationMillis"]) / 1000,
	}

	if db.selectAllConditional("streamdetails", f"idFile='{fileID}' AND iStreamType='0'"):
		db.update("streamdetails", data, f"idFile='{fileID}' AND iStreamType='0'")
	else:
		db.insert("streamdetails", data)

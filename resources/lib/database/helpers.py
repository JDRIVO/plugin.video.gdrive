import os
import re
from sqlite3 import dbapi2 as sqlite

import xbmc
import xbmcvfs


def getVideoDB():
	dbVersion = {
		"19": "119",
		"20": "121",
	}
	userAgent = xbmc.getUserAgent()
	kodiVersion = re.findall("Kodi\/(\d+)", userAgent)[0]
	return os.path.join(xbmcvfs.translatePath("special://database"), "MyVideos" + dbVersion[kodiVersion] + ".db")

def updateLibrary(filePath, metadata):
	dirPath, filename = os.path.split(filePath)
	selectStatement = "SELECT idFile FROM files WHERE idPath=(SELECT idPath FROM path WHERE strPath='{}') AND strFilename='{}'".format(dirPath + os.sep, filename)
	dbPath = getVideoDB()

	db = sqlite.connect(dbPath)
	query = list(db.execute(selectStatement))
	db.close()

	if not query:
		return

	fileID = query[0][0]
	videoDuration = float(metadata["durationMillis"]) / 1000
	videoWidth = metadata["width"]
	videoHeight = metadata["height"]
	aspectRatio = float(videoWidth) / videoHeight

	p1 = "INSERT INTO streamdetails (iVideoWidth, iVideoHeight, fVideoAspect, iVideoDuration, idFile, iStreamType)"
	p2 = "SELECT '{}', '{}', '{}', '{}', {}, '0'".format(videoWidth, videoHeight, aspectRatio, videoDuration, fileID)
	p3 = "WHERE NOT EXISTS (SELECT 1 FROM streamdetails WHERE iVideoWidth='{}' AND iVideoHeight='{}' AND fVideoAspect='{}' AND iVideoDuration='{}' AND idFile='{}' AND iStreamType='0')".format(videoWidth, videoHeight, aspectRatio, videoDuration, fileID)

	insertStatement = "{} {} {}".format(p1, p2, p3)
	db = sqlite.connect(dbPath)
	db.execute(insertStatement)
	db.commit()
	db.close()

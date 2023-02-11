import os
import re
import math
import html
import difflib

from .. import ptn
from .. import network

SUBTITLES = (
	"srt",
	"ssa",
	"vtt",
	"sub",
	"ttml",
	"sami",
	"ass",
	"idx",
	"sbv",
	"stl",
	"smi",
)

VIDEO_FILE_EXTENSIONS = (
	"webm",
	"mkv",
	"flv",
	"vob",
	"ogv",
	"ogg",
	"rrc",
	"gifv",
	"mng",
	"mov",
	"avi",
	"qt",
	"wmv",
	"yuv",
	"rm",
	"asf",
	"amv",
	"mp4",
	"m4p",
	"m4v",
	"mpg",
	"mp2",
	"mpeg",
	"mpe",
	"mpv",
	"m4v",
	"svi",
	"3gp",
	"3g2",
	"mxf",
	"roq",
	"nsv",
	"flv",
	"f4v",
	"f4p",
	"f4a",
	"f4b",
	"mod",
)


def removeProhibitedFSchars(name):
	return re.sub('[<>\*\?\\/:|"]*', '', name)

def generateFilePath(dirPath, filename):
	return duplicateFileCheck(dirPath, filename)

def duplicateFileCheck(dirPath, filename):
	filePath = os.path.join(dirPath, filename)
	filename, fileExtension = os.path.splitext(filename)
	copy = 1

	while os.path.exists(filePath):
		filePath = os.path.join(dirPath, "{} ({}){}".format(filename, copy, fileExtension))
		copy += 1

	return filePath

def identifyFileType(filename, fileExtension, mimeType):

	if mimeType == "application/vnd.google-apps.folder":
		return "folder"

	if not fileExtension:
		return

	fileExtension = fileExtension.lower()

	if "video" in mimeType or fileExtension in VIDEO_FILE_EXTENSIONS:
		return "video"
	elif fileExtension == "nfo":
		return "nfo"
	elif fileExtension == "jpg":
		fileNameLowerCase = filename.lower()

		if "poster" in fileNameLowerCase:
			return "poster"
		elif "fanart" in fileNameLowerCase:
			return "fanart"

	elif fileExtension in SUBTITLES:
		return "subtitles"
	elif fileExtension == "strm":
		return "strm"

def identifyMediaType(videoInfo):
	videoTitle = videoInfo.get("title")
	videoYear = videoInfo.get("year")
	videoSeason = videoInfo.get("season")
	videoEpisode = videoInfo.get("episode")

	if videoEpisode is not None and videoSeason is not None and videoTitle:
		return "episode"
	elif videoTitle and videoYear:
		return "movie"

def getVideoInfo(filename, metadata):

	try:
		videoDuration = float(metadata["durationMillis"]) / 1000
		videoWidth = metadata["width"]
		videoHeight = metadata["height"]
		aspectRatio = float(videoWidth) / videoHeight
	except Exception:
		videoDuration = False
		videoWidth = False
		videoHeight = False
		aspectRatio = False

	videoInfo = ptn.parse(filename, standardise=True, coherent_types=False)
	title = videoInfo.get("title")
	year = videoInfo.get("year")
	season = videoInfo.get("season")
	episode = videoInfo.get("episode")

	videoCodec = videoInfo.get("codec")
	hdr = videoInfo.get("hdr")
	audioCodec = videoInfo.get("audio")
	audioChannels = False

	if audioCodec:
		audioCodecList = audioCodec.split(" ")

		if len(audioCodecList) > 1:
			audioCodec = audioCodecList[0]
			audioChannels = int(math.ceil(float(audioCodecList[1])))

	return {
		"title": title,
		"year": year,
		"season": season,
		"episode": episode,
		"video_width": videoWidth,
		"video_height": videoHeight,
		"aspect_ratio": aspectRatio,
		"video_duration": videoDuration,
		"video_codec": videoCodec,
		"audio_codec": audioCodec,
		"audio_channels": audioChannels,
		"hdr": hdr,
	}

def createSTRMContents(driveID, fileID, encrypted, contents):
	contents["drive_id"] = driveID
	contents["file_id"] = fileID
	contents["encrypted"] = str(encrypted)
	return "plugin://plugin.video.gdrive/?mode=video" + "".join(["&{}={}".format(k, v) for k, v in contents.items() if v])

def getTMDBtitle(type, title, year):
	url = "https://www.themoviedb.org/search/"

	if year:
		params = {"query": "{} y:{}".format(title, year)}
	else:
		params = {"query": title}

	if type == "episode":
		url += "tv"
	else:
		url += "movie"

	response = network.requester.sendPayload(network.helpers.addQueryString(url, params))

	try:
		tmdbResult = re.findall('class="result".*?<h2>(.*?)</h2></a>.*?([\d]{4})', response, re.DOTALL)
	except Exception:
		return

	if not tmdbResult and year:
		response = network.requester.sendPayload(network.helpers.addQueryString(url, params))

		try:
			tmdbResult = re.findall('class="result".*?<h2>(.*?)</h2></a>.*?([\d]{4})', response, re.DOTALL)
		except Exception:
			return

	if not tmdbResult:
		return

	tmdbTitle, tmdbYear = tmdbResult[0]
	tmdbTitle = removeProhibitedFSchars(html.unescape(tmdbTitle))
	titleLowerCase = title.lower()

	tmdbTitleLowerCase = tmdbTitle.lower()
	title = title.lower()
	titleSimilarity = difflib.SequenceMatcher(None, titleLowerCase, tmdbTitleLowerCase).ratio()

	if titleSimilarity > 0.85 or tmdbTitleLowerCase in titleLowerCase or titleLowerCase in tmdbTitleLowerCase:
		return tmdbTitle, tmdbYear

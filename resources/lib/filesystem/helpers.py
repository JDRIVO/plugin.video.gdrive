import os
import re
import math
import html
import difflib

from .. import ptn
from . import video
from .file import File
from .. import library
from .. import network
from .. import filesystem
from .subtitles import Subtitles

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
	return re.sub(r'[<>\*\?\\/:|"]*', '', name)

def generateFilePath(dirPath, filename):
	return duplicateFileCheck(dirPath, filename)

def duplicateFileCheck(dirPath, filename):
	filePath = os.path.join(dirPath, filename)
	filename, fileExtension = os.path.splitext(filename)
	copy = 1

	while os.path.exists(filePath):
		filePath = os.path.join(dirPath, f"{filename} ({copy}){fileExtension}")
		copy += 1

	return filePath

def identifyFileType(filename, fileExtension, mimeType):

	if not fileExtension:
		return

	fileExtension = fileExtension.lower()

	if "video" in mimeType or fileExtension in VIDEO_FILE_EXTENSIONS:
		return "video"
	elif fileExtension == "nfo":
		return "nfo"
	elif fileExtension == "jpg":
		filenameLowerCase = filename.lower()

		if "poster" in filenameLowerCase:
			return "poster"
		elif "fanart" in filenameLowerCase:
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
	language = videoInfo.get("language")

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
		"language": language,
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
	return "plugin://plugin.video.gdrive/?mode=video" + "".join([f"&{k}={v}"for k, v in contents.items() if v])

def getTMDBtitle(type, title, year):
	url = "https://www.themoviedb.org/search/"

	if year:
		params = {"query": f"{title} y:{year}"}
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
		params = {"query": title}
		response = network.requester.sendPayload(network.helpers.addQueryString(url, params))

		try:
			tmdbResult = re.findall('class="result".*?<h2>(.*?)</h2></a>.*?([\d]{4})', response, re.DOTALL)
		except Exception:
			return

		try:
			tmdbTitle, tmdbYear = tmdbResult[0]
		except ValueError:
			return

		tmdbYearInt = int(tmdbYear)

		if abs(tmdbYearInt - year) > 1:
			return

	elif not tmdbResult:
		return

	titleLowerCase = title.lower()

	for result in tmdbResult[0:3]:

		try:
			tmdbTitle, tmdbYear = result
		except ValueError:
			return

		tmdbTitle = removeProhibitedFSchars(html.unescape(tmdbTitle))
		tmdbTitleLowerCase = tmdbTitle.lower()
		titleSimilarity = difflib.SequenceMatcher(None, titleLowerCase, tmdbTitleLowerCase).ratio()
		tmdbYearInt = int(tmdbYear)

		if titleSimilarity > 0.85:

			if year and abs(tmdbYearInt - year) <= 1:
				return tmdbTitle, year
			else:
				return tmdbTitle, tmdbYear

		elif (tmdbTitleLowerCase in titleLowerCase or titleLowerCase in tmdbTitleLowerCase) and year:

			if abs(tmdbYearInt - year) <= 1:
				return tmdbTitle, tmdbYear

def makeFile(file, excludedTypes, encrypter):
	fileID = file["id"]
	filename = file["name"]
	mimeType = file["mimeType"]
	fileExtension = file.get("fileExtension")
	metadata = file.get("videoMediaMetadata")

	if encrypter and mimeType == "application/octet-stream" and not fileExtension:
		filename = encrypter.decryptFilename(filename)

		if not filename:
			return

		fileExtension = filename.rsplit(".", 1)[-1]
		encrypted = True

	else:
		encrypted = False

	fileType = identifyFileType(filename, fileExtension, mimeType)

	if not fileType or fileType in excludedTypes:
		return

	if fileType != "strm":
		videoInfo = getVideoInfo(filename, metadata)
		mediaType = identifyMediaType(videoInfo)

		if fileType == "subtitles":
			file = Subtitles()
		elif mediaType == "episode":
			file = video.Episode()
		elif mediaType == "movie":
			file = video.Movie()
		else:
			file = video.Video()

		file.setContents(videoInfo)
		file.metadata = metadata
	else:
		file = File()

	filename = removeProhibitedFSchars(filename)
	file.name = filename
	file.id = fileID
	file.type = fileType
	file.encrypted = encrypted
	file.removeFileExtension()
	return file

def getExcludedTypes(folderSettings):
	excluded = []

	if not folderSettings["sync_subtitles"]:
		excluded.append("subtitles")

	if not folderSettings["sync_artwork"]:
		excluded.append("poster")
		excluded.append("fanart")

	if not folderSettings["sync_nfo"]:
		excluded.append("nfo")

	return excluded

def refreshMetadata(metadata, strmPath):
	fileOperations = filesystem.operations.FileOperations()
	strmContent = fileOperations.readFile(strmPath)
	strmContent += f"&video_width={metadata['width']}&video_height={metadata['height']}&aspect_ratio={float(metadata['width']) / metadata['height']}&video_duration={float(metadata['durationMillis']) / 1000}"
	fileOperations.overwriteFile(strmPath, strmContent)
	library.helpers.updateLibrary(strmPath, metadata)

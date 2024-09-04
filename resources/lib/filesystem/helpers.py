import os
import re
import math
import time
import difflib
import datetime

from .. import ptn
from . import video
from .file import File
from .. import network
from .constants import *
from .subtitles import Subtitles


def convertTime(time):
	# RFC 3339 to timestamp
	return datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc).timestamp()

def createSTRMContents(driveID, fileID, encrypted, contents):
	contents.update({"drive_id": driveID, "file_id": fileID, "encrypted": str(encrypted)})
	return "plugin://plugin.video.gdrive/?mode=video" + "".join([f"&{k}={v}"for k, v in contents.items() if v])

def duplicateFileCheck(dirPath, filename, creationDate=None):
	filePath = os.path.join(dirPath, filename)
	filename, fileExtension = os.path.splitext(filename)
	copy = 1

	while os.path.exists(filePath):

		if creationDate and creationDate == getCreationDate(filePath):
			break

		filePath = os.path.join(dirPath, f"{filename} ({copy}){fileExtension}")
		copy += 1

	return filePath

def generateFilePath(dirPath, filename):
	return duplicateFileCheck(dirPath, filename)

def getCreationDate(path):

	if os.name == "nt":
		return os.path.getctime(path)
	else:
		stat = os.stat(path)

		try:
			return stat.st_birthtime
		except AttributeError:
			return stat.st_mtime

def getExcludedTypes(folderSettings):
	excluded = []

	if not folderSettings["sync_subtitles"]:
		excluded.append("subtitles")

	if not folderSettings["sync_artwork"]:
		excluded += list(ARTWORK)

	if not folderSettings["sync_nfo"]:
		excluded.append("nfo")

	return excluded

def getTMDBtitle(type, title, year, tmdbSettings, imdbLock):

	def findMatch():

		for result in apiMatches:
			tmdbTitle, tmdbYear = result
			tmdbTitle = removeProhibitedFSchars(tmdbTitle)
			tmdbTitleLowerCase = tmdbTitle.replace(" ", "").casefold()
			titleSimilarity = difflib.SequenceMatcher(None, titleLowerCase, tmdbTitleLowerCase).ratio()
			tmdbYearInt = int(tmdbYear)

			if titleSimilarity in matches:
				matchesYear = matches[titleSimilarity][1]

				if not year or matchesYear == yearStr or abs(int(matchesYear) - year) < 2:
					continue

			if titleSimilarity >= 0.5 or totalResults == 1:

				if year and abs(tmdbYearInt - year) > 1:
					continue
				else:
					matches[titleSimilarity] = tmdbTitle, tmdbYear

			elif tmdbTitleLowerCase in titleLowerCase or titleLowerCase in tmdbTitleLowerCase:

				if year and abs(tmdbYearInt - year) < 2 or not year:
					matches[titleSimilarity] = tmdbTitle, tmdbYear

	def getMatches(url, query, movie):
		matches = []
		delay = 2
		attempts = 3
		response = None

		for _ in range(attempts):

			try:
				response = network.requester.makeRequest(query)

				if response:
					break

			except Exception:
				pass

			time.sleep(delay)

		if not response:
			return

		totalResults = response["total_results"]

		for result in response["results"][:3]:

			if movie:
				title = result["title"]
				year = result["release_date"][:4]
				originalTitle = result["original_title"]
			else:
				title = result["name"]
				year = result["first_air_date"][:4]
				originalTitle = result["original_name"]

			if not title or not year:
				continue

			if (title, year) not in matches:
				matches.append((title, year))

			if (originalTitle, year) not in matches:
				matches.append((originalTitle, year))

		return totalResults, matches

	url = "https://api.themoviedb.org/3/search/"

	if type == "movie":
		url += "movie"
		movie = True
	else:
		url += "tv"
		movie = False

	queries = (
		network.helpers.addQueryString(url, {"query": title, "year" if movie else "first_air_date_year": year, **tmdbSettings}),
		network.helpers.addQueryString(url, {"query": title, **tmdbSettings}),
	)

	if year:
		query = queries[0]
	else:
		query = queries[1]

	totalResults, apiMatches = getMatches(url, query, movie)
	titleLowerCase = title.replace(" ", "").casefold()
	yearStr = str(year)
	matches = {}

	if apiMatches:
		findMatch()

	if year and (not matches or totalResults > 1 and max(matches) < 0.85):
		totalResults, apiMatches = getMatches(url, queries[1], movie)
		findMatch()

	if matches:
		highestTitleSimilarity = max(matches)

		if not movie or highestTitleSimilarity >= 0.85:
			return matches[highestTitleSimilarity]

	if not movie:
		return

	url = "https://www.imdb.com/find/"
	queries = []
	params = {
		"s": "tt",
		"ttype": "ft",
		"ref_": "fn_ft",
	}
	query = network.helpers.addQueryString(url, {"q": f"{title} {year}", **params})
	apiMatches = None

	with imdbLock:
		delay = 2
		attempts = 3

		for _ in range(attempts):

			try:
				response = network.requester.makeRequest(query)

				if response:
					apiMatches = re.search('"titleNameText":"(.*?)".*?"titleReleaseText":"(.*?)"', response)
					break

			except Exception:
				pass

			time.sleep(delay)

		time.sleep(1)

	if apiMatches:
		imdbTitle, imdbYear = apiMatches.group(1, 2)
		apiMatches = [(re.sub(r"\\u([0-9a-fA-F]{4})", lambda x: chr(int(x.group(1), 16)), imdbTitle), imdbYear)]
		findMatch()

	if matches:
		return matches[max(matches)]

def makeFile(file, excludedTypes, encrypter):
	fileID = file["id"]
	filename = file["name"]
	mimeType = file["mimeType"]
	modifiedTime = file["modifiedTime"]
	fileExtension = file.get("fileExtension")
	metadata = file.get("videoMediaMetadata", {})

	if encrypter and mimeType == "application/octet-stream" and not fileExtension:
		filename = encrypter.decryptFilename(filename)

		if not filename:
			return

		fileExtension = filename.rsplit(".", 1)[-1]
		encrypted = True

	else:
		encrypted = False

	fileType = _identifyFileType(filename, fileExtension, mimeType)

	if not fileType or fileType in excludedTypes:
		return

	if fileType == "strm":
		file = File()
	else:
		ptnData = ptn.parse(filename, standardise=True, coherent_types=False)
		videoData = _identifyVideo(ptnData)
		media = videoData["media"]
		metadata = _extractMetadata(metadata, ptnData)

		if fileType == "subtitles":
			file = Subtitles()
		elif media == "episode":
			file = video.Episode()
		elif media == "movie":
			file = video.Movie()
		else:
			file = video.Video()

		file.media = media
		file.setData(videoData, metadata)

	filename = removeProhibitedFSchars(filename)
	file.name = filename
	file.id = fileID
	file.type = fileType
	file.encrypted = encrypted
	file.extension = fileExtension
	file.modifiedTime = convertTime(modifiedTime)
	return file

def removeProhibitedFSchars(name):
	return re.sub(r'[<>\*\?\\/:|"]*', '', name.rstrip())

def _extractMetadata(metadata, ptnData):
	duration = metadata.get("durationMillis")
	videoWidth = metadata.get("width")
	videoHeight = metadata.get("height")
	audioCodec = ptnData.get("audio")
	audioChannels = None

	if audioCodec:
		audioCodecList = audioCodec.split(" ")

		if len(audioCodecList) > 1:
			audioCodec = audioCodecList[0]
			audioChannels = int(math.ceil(float(audioCodecList[1])))

	return {
		"video_duration": float(duration) / 1000 if duration else None,
		"video_width": videoWidth,
		"video_height": videoHeight,
		"aspect_ratio": float(videoWidth) / videoHeight if videoWidth and videoHeight else None,
		"video_codec": ptnData.get("codec"),
		"audio_codec": audioCodec,
		"audio_channels": audioChannels,
		"hdr": ptnData.get("hdr"),
	}

def _identifyFileType(filename, fileExtension, mimeType):

	if not fileExtension:
		return

	fileExtension = fileExtension.lower()

	if "video" in mimeType or fileExtension in VIDEO_EXTENSIONS:
		return "video"
	elif fileExtension == "nfo":
		return "nfo"
	elif fileExtension in ("jpeg", "jpg", "png"):
		return next((type for type in MEDIA_ASSETS if type in filename.lower()), None)
	elif fileExtension in SUBTITLE_EXTENSIONS:
		return "subtitles"
	elif fileExtension == "strm":
		return "strm"

def _identifyVideo(ptnData):
	title = ptnData.get("title")
	year = ptnData.get("year")
	season = ptnData.get("season")
	episode = ptnData.get("episode")
	language = ptnData.get("language")
	media = None

	if episode is not None and season is not None and title:
		media = "episode"
	elif title and year:
		media = "movie"

	return {
		"media": media,
		"title": title,
		"year": year,
		"season": season,
		"episode": episode,
		"language": language,
	}

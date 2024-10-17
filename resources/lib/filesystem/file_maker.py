import math

from .file import File
from .video import Episode, Movie, Video
from .fs_helpers import removeProhibitedFSchars
from .fs_constants import IMAGE_EXTENSIONS, MEDIA_ASSETS, SUBTITLE_EXTENSIONS, VIDEO_EXTENSIONS
from .. import ptn
from helpers import rfcToTimestamp


def makeFile(fileData, excludedTypes, encryptor):
	filename = fileData["name"]
	mimeType = fileData["mimeType"]
	fileExtension = fileData.get("fileExtension")

	if encryptor and mimeType == "application/octet-stream" and not fileExtension:
		filename = encryptor.decryptFilename(filename)

		if not filename:
			return

		fileExtension = filename.rsplit(".", 1)[-1]
		encrypted = True

	else:

		if not fileExtension:
			return

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
		metadata = _extractMetadata(fileData.get("videoMediaMetadata", {}), ptnData)

		if media == "movie":
			file = Movie()
		elif media == "episode":
			file = Episode()
		else:
			file = Video()

		file.media = media
		file.setData(videoData, metadata)

	filename = removeProhibitedFSchars(filename)
	file.remoteName = filename
	file.id = fileData["id"]
	file.type = fileType
	file.encrypted = encrypted
	file.extension = fileExtension
	file.modifiedTime = rfcToTimestamp(fileData["modifiedTime"])
	return file

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
	fileExtension = fileExtension.lower()

	if "video" in mimeType or fileExtension in VIDEO_EXTENSIONS:
		return "video"
	elif fileExtension == "nfo":
		return "nfo"
	elif fileExtension in SUBTITLE_EXTENSIONS:
		return "subtitles"
	elif fileExtension in IMAGE_EXTENSIONS:
		return next((type for type in MEDIA_ASSETS if type in filename.lower()), None)
	elif fileExtension == "strm":
		return "strm"

def _identifyVideo(ptnData):
	title = ptnData.get("title")
	year = ptnData.get("year", False)
	season = ptnData.get("season")
	episode = ptnData.get("episode")
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
		"language": ptnData.get("language"),
	}

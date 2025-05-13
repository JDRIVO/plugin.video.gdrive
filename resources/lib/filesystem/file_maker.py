import math

from helpers import rfcToTimestamp
from .file import File
from .video import Episode, Movie, Video
from .fs_helpers import removeProhibitedFSchars
from .fs_constants import ARTWORK, IMAGE_EXTENSIONS, SUBTITLE_EXTENSIONS, VIDEO_EXTENSIONS
from .. import ptn


def makeFile(fileData, excludedTypes, prefix, suffix, encryptor):
	filename = fileData["name"]
	mimeType = fileData["mimeType"]
	fileExtension = fileData.get("fileExtension")
	encryptionID = None

	if encryptor:
		decryptedFilename = encryptor.decryptFilename(filename, fileExtension, mimeType)

		if not decryptedFilename:
			return

		if decryptedFilename != filename:
			filename = decryptedFilename
			fileExtension = filename.rsplit(".", 1)[-1]

			if encryptor.encryptData and mimeType == "application/octet-stream":
				encryptionID = encryptor.profile.id

	elif not fileExtension:
		return

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
		file.setData(videoData, metadata, prefix, suffix)

	filename = removeProhibitedFSchars(filename)
	file.remoteName = filename
	file.id = fileData["id"]
	file.type = fileType
	file.encryptionID = encryptionID
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
		filename = filename.lower()
		return next((type for type in ARTWORK if type in filename), None)
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

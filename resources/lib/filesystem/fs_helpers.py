import os
import re

from .fs_constants import ARTWORK


def duplicateFileCheck(dirPath, filename, filePath=None):
	filePath = filePath or os.path.join(dirPath, filename)
	filePathLower = filePath.lower()
	filename, fileExtension = os.path.splitext(filename)
	copy = 1

	while os.path.exists(filePath):
		filePath = os.path.join(dirPath, f"{filename} ({copy}){fileExtension}")

		if filePathLower == filePath.lower():
			break

		copy += 1

	return filePath

def generateFilePath(dirPath, filename):
	return duplicateFileCheck(dirPath, filename)

def getExcludedTypes(folderSettings):
	excluded = []

	if not folderSettings["sync_subtitles"]:
		excluded.append("subtitles")

	if not folderSettings["sync_artwork"]:
		excluded += list(ARTWORK)

	if not folderSettings["sync_nfo"]:
		excluded.append("nfo")

	if not folderSettings["sync_strm"]:
		excluded.append("strm")

	return excluded

def removeProhibitedFSchars(name):
	return re.sub(r'[<>\*\?\\/:|"]*', '', name.rstrip())

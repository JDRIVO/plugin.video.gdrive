import os
import re

from .fs_constants import ARTWORK


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

	if not folderSettings["sync_strm"]:
		excluded.append("strm")

	return excluded

def removeProhibitedFSchars(name):
	return re.sub(r'[<>\*\?\\/:|"]*', '', name.rstrip())

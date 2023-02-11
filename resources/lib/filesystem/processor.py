import os

from . import helpers
from .. import database


class FileProcessor:

	def __init__(self, cloudService, fileOperations, settings):
		self.cloudService = cloudService
		self.fileOperations = fileOperations
		self.settings = settings

	def processMediaAssets(self, mediaExtras, videoFilename, newVideoFilename, fileExtension, dirPath, videoRenamed, originalPath, cachedFiles, folderID, subtitles=False):

		for mediaExtra in list(mediaExtras):
			filename = mediaExtra.name

			if videoFilename in filename:

				if videoRenamed:

					if subtitles:
						_, fileExtension = os.path.splitext(filename)
						newFilename = f"{newVideoFilename}{fileExtension}"
					else:
						newFilename = newVideoFilename + fileExtension

					filePath = helpers.generateFilePath(dirPath, newFilename)
					originalName = False
					originalFolder = True if originalPath else False
				else:
					filePath = helpers.generateFilePath(dirPath, filename)
					originalName = True
					originalFolder = True if originalPath else False

				fileID = mediaExtra.id
				self.fileOperations.downloadFile(dirPath, filePath, fileID)
				mediaExtras.remove(mediaExtra)
				cachedFiles[fileID]  = {
					"local_name": os.path.basename(filePath),
					"remote_name": filename,
					"local_path": filePath if not originalFolder else False,
					"parent_folder_id": folderID,
					"original_name": originalName,
					"original_folder": originalFolder,
				}


	def processFiles(self, cachedDirectories, cachedFiles, files, folderSettings, remotePath, strmRoot, driveID, parentFolderID):
		folderStructure = folderSettings["folder_structure"]
		fileRenaming = folderSettings["file_renaming"]
		syncNFO = folderSettings["sync_nfo"]
		syncArtwork = folderSettings["sync_artwork"]
		syncSubtitles = folderSettings["sync_subtitles"]

		videos = files.get("video")
		subtitles = files.get("subtitles")
		fanart = files.get("fanart")

		posters = files.get("poster")
		nfos = files.get("nfo")
		strm = files.get("strm")

		fileIDs = cachedDirectories[parentFolderID]["file_ids"]

		for video in videos:
			filenameWithoutExtension = video.removeFileExtension()
			filename = video.name
			fileID = video.id
			videoMetadata = video.metadata

			refreshMetadata = video.refresh_metadata
			strmContent = helpers.createSTRMContents(driveID, fileID, video.encrypted, video.contents)

			dirPath = remotePath
			newFilename = videoRenamed = strmPath = False
			originalPath = True

			if folderStructure != "original" or fileRenaming != "original":

				if str(video) in ("Episode", "Movie"):
					modifiedName = video.formatName()
					newFilename = modifiedName.get("filename") if modifiedName else False

				if folderStructure != "original" and newFilename:

					if str(video) == "Movie":
						dirPath = os.path.join(strmRoot, "[gDrive] Movies")

						if fileRenaming != "original":
							strmPath = helpers.generateFilePath(dirPath, newFilename + ".strm")
							videoRenamed = True
						else:
							strmPath = helpers.generateFilePath(dirPath, filenameWithoutExtension + ".strm")

					elif str(video) == "Episode":
						dirPath = os.path.join(strmRoot, "[gDrive] TV", modifiedName["title"], "Season " + video.season)

						if fileRenaming != "original":
							strmPath = helpers.generateFilePath(dirPath, newFilename + ".strm")
							videoRenamed = True
						else:
							strmPath = helpers.generateFilePath(dirPath, filenameWithoutExtension + ".strm")

					originalPath = False

				elif fileRenaming != "original" and newFilename:
					strmPath = helpers.generateFilePath(dirPath, newFilename + ".strm")
					videoRenamed = True

				if syncSubtitles and subtitles:
					self.processMediaAssets(subtitles, filenameWithoutExtension, newFilename, None, dirPath, videoRenamed, originalPath, cachedFiles, parentFolderID, subtitles=True)

				if syncArtwork:

					if fanart:
						self.processMediaAssets(fanart, filenameWithoutExtension, newFilename, "-fanart.jpg", dirPath, videoRenamed, originalPath, cachedFiles, parentFolderID)

					if posters:
						self.processMediaAssets(posters, filenameWithoutExtension, newFilename, "-poster.jpg", dirPath, videoRenamed, originalPath, cachedFiles, parentFolderID)

				if syncNFO and nfos:
					self.processMediaAssets(nfos, filenameWithoutExtension, newFilename, ".nfo", dirPath, videoRenamed, originalPath, cachedFiles, parentFolderID)

			if not strmPath:
				strmPath = helpers.generateFilePath(dirPath, filenameWithoutExtension + ".strm")

			self.fileOperations.createFile(dirPath, strmPath, strmContent, mode="w+")

			if refreshMetadata:
				database.helpers.updateLibrary(strmPath, videoMetadata)

			originalName = False if videoRenamed else True
			originalFolder = True if originalPath else False

			cachedFiles[fileID] = {
				"local_name": os.path.basename(strmPath),
				"remote_name": filename,
				"local_path": strmPath if not originalFolder else False,
				"parent_folder_id": parentFolderID,
				"original_name": originalName,
				"original_folder": originalFolder,
			}

			if fileID not in fileIDs:
				fileIDs.append(fileID)

		unaccountedFiles = []

		if syncSubtitles and subtitles:
			unaccountedFiles += subtitles

		if syncArtwork and (fanart or posters):

			if fanart:
				unaccountedFiles += fanart

			if posters:
				unaccountedFiles += posters

		if syncNFO and nfos:
			unaccountedFiles += nfos

		if strm:
			unaccountedFiles += strm

		if unaccountedFiles:
			self.fileOperations.downloadFiles(unaccountedFiles, remotePath, cachedFiles, parentFolderID, fileIDs)

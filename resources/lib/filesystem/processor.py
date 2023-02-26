import os

from . import helpers
from .. import library


class FileProcessor:

	def __init__(self, cloudService, fileOperations, settings, cache):
		self.cloudService = cloudService
		self.fileOperations = fileOperations
		self.settings = settings
		self.cache = cache

	def processMediaAssets(
		self,
		mediaAssets,
		videoFilename,
		newVideoFilename,
		fileExtension,
		dirPath,
		videoRenamed,
		originalPath,
		driveID,
		folderID,
		rootFolderID,
		syncRootPath,
		subtitles=False
	):

		for mediaAsset in list(mediaAssets):
			filename = mediaAsset.name

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

				fileID = mediaAsset.id
				self.fileOperations.downloadFile(dirPath, filePath, fileID)
				mediaAssets.remove(mediaAsset)
				file = {
					"file_id": fileID,
					"drive_id": driveID,
					"local_path": filePath.replace(syncRootPath, "") if not originalFolder else False,
					"parent_folder_id": folderID,
					"root_folder_id": rootFolderID,
					"local_name": os.path.basename(filePath),
					"remote_name": filename,
					"original_name": originalName,
					"original_folder": originalFolder,
				}
				self.cache.insert("files", file)

	def processFiles(
		self,
		files,
		folderSettings,
		remotePath,
		syncRootPath,
		driveID,
		parentFolderID,
		rootFolderID,
	):
		folderRestructure = folderSettings["folder_restructure"]
		fileRenaming = folderSettings["file_renaming"]
		syncNFO = folderSettings["sync_nfo"]
		syncArtwork = folderSettings["sync_artwork"]
		syncSubtitles = folderSettings["sync_subtitles"]
		syncRootPath = syncRootPath + os.sep

		videos = files.get("video")
		subtitles = files.get("subtitles")
		fanart = files.get("fanart")

		posters = files.get("poster")
		nfos = files.get("nfo")
		strm = files.get("strm")

		if videos:
			videos.reverse()

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

			if folderRestructure or fileRenaming:

				if str(video) in ("Episode", "Movie"):
					modifiedName = video.formatName()
					newFilename = modifiedName.get("filename") if modifiedName else False

				if folderRestructure and newFilename:

					if str(video) == "Movie":
						dirPath = os.path.join(syncRootPath, "[gDrive] Movies")

						if fileRenaming:
							dirPath = os.path.join(dirPath, newFilename)
							strmPath = helpers.generateFilePath(
								dirPath,
								newFilename + ".strm",
							)
							videoRenamed = True
						else:
							strmPath = helpers.generateFilePath(
								dirPath,
								filenameWithoutExtension + ".strm",
							)

					elif str(video) == "Episode":
						dirPath = os.path.join(
							syncRootPath,
							"[gDrive] TV",
							modifiedName["title"],
							"Season " + video.season,
						)

						if fileRenaming:
							strmPath = helpers.generateFilePath(dirPath, newFilename + ".strm")
							videoRenamed = True
						else:
							strmPath = helpers.generateFilePath(dirPath, filenameWithoutExtension + ".strm")

					originalPath = False

				elif fileRenaming and newFilename:
					strmPath = helpers.generateFilePath(dirPath, newFilename + ".strm")
					videoRenamed = True

				if syncSubtitles and subtitles:
					self.processMediaAssets(
						subtitles,
						filenameWithoutExtension,
						newFilename,
						None,
						dirPath,
						videoRenamed,
						originalPath,
						driveID,
						parentFolderID,
						rootFolderID,
						syncRootPath,
						subtitles=True,
					)

				if syncArtwork:

					if fanart:
						self.processMediaAssets(
							fanart,
							filenameWithoutExtension,
							newFilename,
							"-fanart.jpg",
							dirPath,
							videoRenamed,
							originalPath,
							driveID,
							parentFolderID,
							rootFolderID,
							syncRootPath,
						)

					if posters:
						self.processMediaAssets(
							posters,
							filenameWithoutExtension,
							newFilename,
							"-poster.jpg",
							dirPath,
							videoRenamed,
							originalPath,
							driveID,
							parentFolderID,
							rootFolderID,
							syncRootPath,
						)

				if syncNFO and nfos:
					self.processMediaAssets(
						nfos,
						filenameWithoutExtension,
						newFilename,
						".nfo",
						dirPath,
						videoRenamed,
						originalPath,
						driveID,
						parentFolderID,
						rootFolderID,
						syncRootPath,
					)

			if not strmPath:
				strmPath = helpers.generateFilePath(dirPath, filenameWithoutExtension + ".strm")

			self.fileOperations.createFile(dirPath, strmPath, strmContent, mode="w+")

			if refreshMetadata:
				library.helpers.updateLibrary(strmPath, videoMetadata)

			originalName = False if videoRenamed else True
			originalFolder = True if originalPath else False

			file = {
				"drive_id": driveID,
				"file_id": fileID,
				"local_path": strmPath.replace(syncRootPath, "") if not originalFolder else False,
				"parent_folder_id": parentFolderID,
				"root_folder_id": rootFolderID,
				"local_name": os.path.basename(strmPath),
				"remote_name": filename,
				"original_name": originalName,
				"original_folder": originalFolder,
			}
			self.cache.insert("files", file)

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

			for file in unaccountedFiles:
				fileID = file.id
				filename = file.name
				encrypted = file.encrypted
				filePath = helpers.generateFilePath(remotePath, filename)

				if encrypted:
					self.fileOperations.downloadFile(remotePath, filePath, fileID, encrypted=True)
				else:
					self.fileOperations.downloadFile(remotePath, filePath, fileID)

				file = {
					"drive_id": driveID,
					"file_id": fileID,
					"local_path": False,
					"parent_folder_id": parentFolderID,
					"root_folder_id": rootFolderID,
					"local_name": os.path.basename(filePath),
					"remote_name": filename,
					"original_name": True,
					"original_folder": True,
				}
				self.cache.insert("files", file)

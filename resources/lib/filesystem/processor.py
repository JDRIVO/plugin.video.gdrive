import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor

from . import helpers
from .. import library
from ..sync import cache


class RemoteFileProcessor:

	def __init__(self, cloudService, fileOperations, settings):
		self.cloudService = cloudService
		self.fileOperations = fileOperations
		self.settings = settings
		self.cache = cache.Cache()
		self.fileLock = threading.Lock()
		self.cacheLock = threading.Lock()

	def processFiles(
		self,
		files,
		folderSettings,
		remoteDirPath,
		syncRootPath,
		driveID,
		rootFolderID,
		parentFolderID,
	):
		syncRootPath = syncRootPath + os.sep
		localDirPath = os.path.join(syncRootPath, remoteDirPath)
		folderRestructure = folderSettings["folder_restructure"]
		fileRenaming = folderSettings["file_renaming"]
		videos = files.get("video")
		mediaAssets = files.get("media_assets")
		strm = files.get("strm")
		cachedFiles = []

		if strm:

			with ThreadPoolExecutor(30) as executor:
				futures = [
					executor.submit(
						self.processSTRM,
						file,
						localDirPath,
						driveID,
						rootFolderID,
						parentFolderID,
						cachedFiles,
					) for file in strm
				]

		if folderRestructure or fileRenaming:
			localDirPath = os.path.join(syncRootPath, "[gDrive] Processing", remoteDirPath)
			originalFolder = False
		else:
			originalFolder = True

		if videos:
			videos.reverse()

			with ThreadPoolExecutor(30) as executor:
				futures = [
					executor.submit(
						self.processVideo,
						video,
						mediaAssets,
						folderSettings,
						localDirPath,
						syncRootPath,
						driveID,
						rootFolderID,
						parentFolderID,
						cachedFiles,
						originalFolder,
					) for video in videos
				]

		if mediaAssets:

			with ThreadPoolExecutor(30) as executor:
				futures = [
					executor.submit(
						self.processMediaAssets,
						assets,
						syncRootPath,
						localDirPath,
						driveID,
						rootFolderID,
						parentFolderID,
						cachedFiles,
						originalFolder,
					) for assetName, assets in mediaAssets.items() if assets
				]

		with self.cacheLock:
			self.cache.addFiles(cachedFiles)

	def processMediaAssets(
		self,
		mediaAssets,
		syncRootPath,
		localDirPath,
		driveID,
		rootFolderID,
		parentFolderID,
		cachedFiles,
		originalFolder,
	):

		for assetType, assets in list(mediaAssets.items()):

			for file in assets:
				remoteName = file.name
				fileID = file.id

				with self.fileLock:
					filePath = helpers.generateFilePath(localDirPath, remoteName)
					self.fileOperations.downloadFile(localDirPath, filePath, fileID, file.encrypted)

				localName = os.path.basename(filePath)
				file.name = localName
				file = (
					driveID,
					rootFolderID,
					parentFolderID,
					fileID,
					filePath.replace(syncRootPath, "") if originalFolder else False,
					localName,
					remoteName,
					True,
					originalFolder,
				)
				cachedFiles.append(file)

	def processSTRM(
		self,
		file,
		localDirPath,
		driveID,
		rootFolderID,
		parentFolderID,
		cachedFiles,
	):
		fileID = file.id
		remoteName = file.name

		with self.fileLock:
			strmPath = helpers.generateFilePath(localDirPath, remoteName)
			self.fileOperations.downloadFile(localDirPath, strmPath, fileID, file.encrypted)

		file = (
			driveID,
			rootFolderID,
			parentFolderID,
			fileID,
			False,
			os.path.basename(strmPath),
			remoteName,
			True,
			True,
		)
		cachedFiles.append(file)

	def processVideo(
		self,
		video,
		mediaAssets,
		folderSettings,
		localDirPath,
		syncRootPath,
		driveID,
		rootFolderID,
		parentFolderID,
		cachedFiles,
		originalFolder,
	):
		remoteName = video.name
		mediaType = video.media
		basename = video.basename
		fileID = video.id
		strmContent = helpers.createSTRMContents(driveID, fileID, video.encrypted, video.contents)
		strmName = f"{basename}.strm"

		with self.fileLock:
			strmPath = helpers.generateFilePath(localDirPath, strmName)
			self.fileOperations.createFile(localDirPath, strmPath, strmContent, mode="w+")

		localName = os.path.basename(strmPath)
		video.basename = localName.replace(".strm", "")
		file = (
			driveID,
			rootFolderID,
			parentFolderID,
			fileID,
			strmPath.replace(syncRootPath, "") if not originalFolder else False,
			localName,
			remoteName,
			True,
			originalFolder,
		)
		cachedFiles.append(file)

class LocalFileProcessor:

	def __init__(self, cloudService, fileOperations, settings):
		self.cloudService = cloudService
		self.fileOperations = fileOperations
		self.settings = settings
		self.cache = cache.Cache()
		self.tmdbLock = threading.Lock()
		self.CacheLock = threading.Lock()
		self.fileLock = threading.Lock()

	def processFiles(
		self,
		files,
		folderSettings,
		remoteDirPath,
		syncRootPath,
		driveID,
		rootFolderID,
		parentFolderID,
	):
		syncRootPath = syncRootPath + os.sep
		processingDirPath = os.path.join(syncRootPath, "[gDrive] Processing", remoteDirPath)
		localDirPath = os.path.join(syncRootPath, remoteDirPath)
		videos = files.get("video")
		mediaAssets = files.get("media_assets")

		if videos:
			videos.reverse()
			folderRestructure = folderSettings["folder_restructure"]
			fileRenaming = folderSettings["file_renaming"]

			with ThreadPoolExecutor(30) as executor:
				futures = [
					executor.submit(
						self.processVideo,
						video,
						mediaAssets,
						folderSettings,
						localDirPath,
						syncRootPath,
						driveID,
						rootFolderID,
						parentFolderID,
						folderRestructure,
						fileRenaming,
						processingDirPath,
					) for video in videos
				]

		if mediaAssets:

			with ThreadPoolExecutor(30) as executor:
				futures = [
					executor.submit(
						self.processMediaAssets,
						assets,
						syncRootPath,
						localDirPath,
						None,
						True,
						True,
						driveID,
						rootFolderID,
						parentFolderID,
						processingDirPath,
					) for assetName, assets in mediaAssets.items() if assets
				]

	def processMediaAssets(
		self,
		mediaAssets,
		syncRootPath,
		localDirPath,
		videoFilename,
		originalName,
		originalFolder,
		driveID,
		rootFolderID,
		parentFolderID,
		processingDirPath,
	):

		for assetType, assets in list(mediaAssets.items()):

			for file in assets:
				remoteFilename = file.name
				fileID = file.id

				if not originalName:

					if assetType == "subtitles":
						language = ""
						_, fileExtension = os.path.splitext(remoteFilename)

						if file.language:
							language += f".{file.language}"

						if re.search("forced\.[\w]*$", remoteFilename, re.IGNORECASE):
							language += ".Forced"

						fileExtension = f"{language}{fileExtension}"

					elif assetType in ("poster", "fanart"):
						fileExtension = f"-{assetType}.jpg"

					localFilename = f"{videoFilename}{fileExtension}"
				else:
					localFilename = remoteFilename

				filePath = os.path.join(processingDirPath, remoteFilename)

				with self.fileLock:
					filePath = self.fileOperations.renameFile(syncRootPath, filePath, localDirPath, localFilename)

				file = {
					"drive_id": driveID,
					"root_folder_id": rootFolderID,
					"parent_folder_id": parentFolderID,
					"file_id": fileID,
					"local_path": filePath.replace(syncRootPath, "") if not originalFolder else False,
					"local_name": os.path.basename(filePath),
					"remote_name": remoteFilename,
					"original_name": originalName,
					"original_folder": originalFolder,
				}

				with self.CacheLock:
					self.cache.updateFile(file, fileID)

			del mediaAssets[assetType]

	def processVideo(
		self,
		video,
		mediaAssets,
		folderSettings,
		localDirPath,
		syncRootPath,
		driveID,
		rootFolderID,
		parentFolderID,
		folderRestructure,
		fileRenaming,
		processingDirPath,
	):
		remoteName = video.name
		mediaType = video.media
		basename = video.basename
		ptnName = video.ptn_name
		fileID = video.id
		strmPath = os.path.join(processingDirPath, f"{basename}.strm")
		strmContent = helpers.createSTRMContents(driveID, fileID, video.encrypted, video.contents)
		originalName = originalFolder = True
		newFilename = False

		if mediaType in ("episode", "movie"):

			with self.tmdbLock:
				modifiedName = video.formatName()

			newFilename = modifiedName.get("filename") if modifiedName else False

		if folderRestructure and newFilename:

			if mediaType == "movie":
				localDirPath = os.path.join(syncRootPath, "[gDrive] Movies", newFilename)

			elif mediaType == "episode":
				localDirPath = os.path.join(
					syncRootPath,
					"[gDrive] Series",
					modifiedName["title"],
					f"Season {video.season}",
				)

			originalFolder = False

		if fileRenaming and newFilename:
			strmName = f"{newFilename}.strm"
			originalName = False
		else:
			strmName = f"{basename}.strm"

		if ptnName in mediaAssets:
			self.processMediaAssets(
				mediaAssets[ptnName],
				syncRootPath,
				localDirPath,
				newFilename,
				originalName,
				originalFolder,
				driveID,
				rootFolderID,
				parentFolderID,
				processingDirPath,
			)

		with self.fileLock:
			strmPath = self.fileOperations.renameFile(syncRootPath, strmPath, localDirPath, strmName)

		file = {
			"drive_id": driveID,
			"root_folder_id": rootFolderID,
			"parent_folder_id": parentFolderID,
			"file_id": fileID,
			"local_path": strmPath.replace(syncRootPath, "") if not originalFolder else False,
			"local_name": os.path.basename(strmPath),
			"remote_name": remoteName,
			"original_name": originalName,
			"original_folder": originalFolder,
		}

		with self.CacheLock:
			self.cache.updateFile(file, fileID)

import os
import re
import threading
from ..threadpool import threadpool

from . import helpers
from .. import library
from .constants import *
from ..sync import cache


class RemoteFileProcessor:

	def __init__(self, cloudService, fileOperations, settings):
		self.cloudService = cloudService
		self.fileOperations = fileOperations
		self.settings = settings
		self.cache = cache.Cache()
		self.fileLock = threading.Lock()

	def processFiles(
		self,
		folder,
		folderSettings,
		remoteDirPath,
		syncRootPath,
		driveID,
		rootFolderID,
		threadCount,
	):
		files = folder.files
		parentFolderID = folder.id
		syncRootPath = syncRootPath + os.sep
		dirPath = os.path.join(syncRootPath, remoteDirPath)
		folderRestructure = folderSettings["folder_restructure"]
		fileRenaming = folderSettings["file_renaming"]
		videos = files.get("video")
		mediaAssets = files.get("media_assets")
		strm = files.get("strm")
		cachedFiles = []

		if strm:

			with threadpool.ThreadPool(threadCount) as pool:
				[
					pool.submit(
						self.processSTRM,
						file,
						dirPath,
						driveID,
						rootFolderID,
						parentFolderID,
						cachedFiles,
					) for file in strm
				]

		if folderRestructure or fileRenaming:
			dirPath = os.path.join(syncRootPath, "[gDrive] Processing", remoteDirPath)
			originalFolder = False
		else:
			originalFolder = True

		if videos:

			with threadpool.ThreadPool(threadCount) as pool:
				[
					pool.submit(
						self.processVideo,
						video,
						syncRootPath,
						dirPath,
						driveID,
						rootFolderID,
						parentFolderID,
						cachedFiles,
						originalFolder,
					) for video in videos
				]

		if mediaAssets:

			with threadpool.ThreadPool(threadCount) as pool:
				[
					pool.submit(
						self.processMediaAssets,
						assets,
						syncRootPath,
						dirPath,
						driveID,
						rootFolderID,
						parentFolderID,
						cachedFiles,
						originalFolder,
					) for assetName, assets in mediaAssets.items() if assets
				]

		self.cache.addFiles(cachedFiles)

	def processMediaAssets(
		self,
		mediaAssets,
		syncRootPath,
		dirPath,
		driveID,
		rootFolderID,
		parentFolderID,
		cachedFiles,
		originalFolder,
	):

		for file in mediaAssets:
			fileID = file.id
			remoteName = file.name
			filePath = helpers.generateFilePath(dirPath, remoteName)
			localName = os.path.basename(filePath)
			file.name = localName
			cacheData = (
				driveID,
				rootFolderID,
				parentFolderID,
				fileID,
				filePath.replace(syncRootPath, "") if not originalFolder else False,
				localName,
				remoteName,
				True,
				originalFolder,
			)
			cachedFiles.append(cacheData)

			with self.fileLock:
				self.fileOperations.downloadFile(dirPath, filePath, fileID, modifiedTime=file.modifiedTime, encrypted=file.encrypted)

	def processSTRM(
		self,
		file,
		dirPath,
		driveID,
		rootFolderID,
		parentFolderID,
		cachedFiles,
	):
		fileID = file.id
		remoteName = file.name
		filePath = helpers.generateFilePath(dirPath, remoteName)
		localName = os.path.basename(filePath)
		cacheData = (
			driveID,
			rootFolderID,
			parentFolderID,
			fileID,
			False,
			localName,
			remoteName,
			True,
			True,
		)
		cachedFiles.append(cacheData)

		with self.fileLock:
			self.fileOperations.downloadFile(dirPath, filePath, fileID, modifiedTime=file.modifiedTime, encrypted=file.encrypted)

	def processVideo(
		self,
		file,
		syncRootPath,
		dirPath,
		driveID,
		rootFolderID,
		parentFolderID,
		cachedFiles,
		originalFolder,
	):
		fileID = file.id
		remoteName = file.name
		filename = f"{file.basename}.strm"
		strmContent = helpers.createSTRMContents(driveID, fileID, file.encrypted, file.contents)
		filePath = helpers.generateFilePath(dirPath, filename)
		localName = os.path.basename(filePath)
		file.name = localName
		cacheData = (
			driveID,
			rootFolderID,
			parentFolderID,
			fileID,
			filePath.replace(syncRootPath, "") if not originalFolder else False,
			localName,
			remoteName,
			True,
			originalFolder,
		)
		cachedFiles.append(cacheData)

		with self.fileLock:
			self.fileOperations.createFile(dirPath, filePath, strmContent, modifiedTime=file.modifiedTime, mode="w+")

class LocalFileProcessor:

	def __init__(self, cloudService, fileOperations, settings):
		self.cloudService = cloudService
		self.fileOperations = fileOperations
		self.settings = settings
		self.cache = cache.Cache()
		self.tmdbLock = threading.Lock()
		self.fileLock = threading.Lock()

	def processFiles(
		self,
		folder,
		folderSettings,
		remoteDirPath,
		syncRootPath,
		threadCount,
	):
		files = folder.files
		syncRootPath = syncRootPath + os.sep
		processingDirPath = os.path.join(syncRootPath, "[gDrive] Processing", remoteDirPath)
		dirPath = os.path.join(syncRootPath, remoteDirPath)
		videos = files.get("video")
		mediaAssets = files.get("media_assets")

		if videos:
			folderRestructure = folderSettings["folder_restructure"]
			fileRenaming = folderSettings["file_renaming"]

			with threadpool.ThreadPool(threadCount) as pool:
				[
					pool.submit(
						self.processVideo,
						video,
						mediaAssets,
						folderSettings,
						syncRootPath,
						dirPath,
						processingDirPath,
						folderRestructure,
						fileRenaming,
					) for video in videos
				]

		if mediaAssets:

			with threadpool.ThreadPool(threadCount) as pool:
				[
					pool.submit(
						self.processMediaAssets,
						assets,
						syncRootPath,
						dirPath,
						processingDirPath,
						None,
						True,
						True,
					) for assetName, assets in mediaAssets.items() if assets
				]

	def processMediaAssets(
		self,
		mediaAssets,
		syncRootPath,
		dirPath,
		processingDirPath,
		videoFilename,
		originalName,
		originalFolder,
	):

		for file in list(mediaAssets):
			fileID = file.id
			remoteName = file.name
			assetType = file.type
			fileExtension = f".{file.extension}"

			if not originalName:

				if assetType == "subtitles":
					language = ""

					if file.language:
						language += f".{file.language}"

					if re.search("forced\.[\w]*$", remoteName, re.IGNORECASE):
						language += ".Forced"

					fileExtension = f"{language}{fileExtension}"

				elif assetType in ARTWORK:
					fileExtension = f"-{assetType}{fileExtension}"

				filename = f"{videoFilename}{fileExtension}"
			else:
				filename = remoteName

			filePath = os.path.join(processingDirPath, remoteName)

			with self.fileLock:
				filePath = self.fileOperations.renameFile(syncRootPath, filePath, dirPath, filename)

			mediaAssets.remove(file)
			file = {
				"local_path": filePath.replace(syncRootPath, "") if not originalFolder else False,
				"local_name": os.path.basename(filePath),
				"original_name": originalName,
				"original_folder": originalFolder,
			}
			self.cache.updateFile(file, fileID)

	def processVideo(
		self,
		file,
		mediaAssets,
		folderSettings,
		syncRootPath,
		dirPath,
		processingDirPath,
		folderRestructure,
		fileRenaming,
	):
		fileID = file.id
		mediaType = file.media
		remoteName = file.name
		ptnName = file.ptn_name
		filename = f"{file.basename}.strm"
		filePath = os.path.join(processingDirPath, filename)
		originalName = originalFolder = True
		newFilename = False

		if mediaType in ("episode", "movie"):

			with self.tmdbLock:
				modifiedName = file.formatName()

			newFilename = modifiedName.get("filename") if modifiedName else False

			if newFilename:

				if fileRenaming:
					filename = f"{newFilename}.strm"
					originalName = False

				if folderRestructure:

					if mediaType == "movie":
						dirPath = os.path.join(syncRootPath, "[gDrive] Movies", newFilename)
					else:
						dirPath = os.path.join(
							syncRootPath,
							"[gDrive] Series",
							modifiedName["title"],
							f"Season {file.season}",
						)

					originalFolder = False

		if ptnName in mediaAssets:
			self.processMediaAssets(
				mediaAssets[ptnName],
				syncRootPath,
				dirPath,
				processingDirPath,
				newFilename,
				originalName,
				originalFolder,
			)

		with self.fileLock:
			filePath = self.fileOperations.renameFile(syncRootPath, filePath, dirPath, filename)

		file = {
			"local_path": filePath.replace(syncRootPath, "") if not originalFolder else False,
			"local_name": os.path.basename(filePath),
			"original_name": originalName,
			"original_folder": originalFolder,
		}
		self.cache.updateFile(file, fileID)

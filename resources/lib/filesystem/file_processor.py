import os
import re
import queue
import threading
import traceback

import xbmc

from .fs_constants import ARTWORK
from ..threadpool.threadpool import ThreadPool
from ..library.library_editor import DatabaseEditor
from ..title_identifier.title_helpers import getTMDBSettings
from ..title_identifier.title_identifier import TitleIdentifier
from ..title_identifier.title_cache_manager import TitleCacheManager

dbEditor = DatabaseEditor()


class RemoteFileProcessor(queue.Queue):

	def __init__(self, fileOperations, cacheUpdater, threadCount, progressDialog=None):
		super().__init__()
		self.fileOperations = fileOperations
		self.cacheUpdater = cacheUpdater
		self.threadCount = threadCount
		self.progressDialog = progressDialog
		self.stop_event = threading.Event()
		self.monitor = xbmc.Monitor()
		self._startWorkers()

	def __enter__(self):
		return self

	def __exit__(self, excType, excValue, excTraceback):
		self.join()
		self.cacheUpdater.addDirectories()
		self.cacheUpdater.addFiles()
		self._stop()

	def addFile(self, data):
		self.put(data)

		if self.progressDialog:
			self.progressDialog.incrementFile()

	def _processMediaAsset(self, file, folder, encryptor):
		dirPath = folder.processingPath or folder.localPath
		filePath = self.fileOperations.downloadFile(dirPath, file.remoteName, file.id, modifiedTime=file.modifiedTime, encrypted=file.encryptionID, encryptor=encryptor)
		localName = os.path.basename(filePath)
		file.localPath = filePath
		file.localName = localName

	def _processSTRM(self, file, folder, encryptor):
		filePath = self.fileOperations.downloadFile(folder.localPath, file.remoteName, file.id, modifiedTime=file.modifiedTime, encrypted=file.encryptionID, encryptor=encryptor)
		localName = os.path.basename(filePath)
		file.localPath = filePath
		file.localName = localName

	def _processVideo(self, file, folder):
		filename = f"{file.basename}.strm"
		strmContent = file.getSTRMContents(folder.driveID)
		dirPath = folder.processingPath or folder.localPath
		filePath = self.fileOperations.createFile(dirPath, filename, strmContent, modifiedTime=file.modifiedTime, mode="w+")
		localName = os.path.basename(filePath)
		file.localPath = filePath
		file.localName = localName

		if file.updateDB and not folder.processingPath:
			dbEditor.processData(filePath, dirPath, localName)

	def _startWorkers(self):
		[threading.Thread(target=self._worker).start() for _ in range(self.threadCount)]

	def _stop(self):
		self.stop_event.set()

	def _stopped(self):
		return self.stop_event.is_set()

	def _worker(self):

		while not self.monitor.abortRequested():

			if self._stopped():
				return

			try:
				file, folder, encryptor = self.get_nowait()

				if file.type == "video":
					self._processVideo(file, folder)
				elif file.type == "media_asset":
					self._processMediaAsset(file, folder, encryptor)
				else:
					self._processSTRM(file, folder, encryptor)

				self.cacheUpdater.addFile(folder, file)

				if self.progressDialog:
					self.progressDialog.processFile(file.remoteName)

				self.task_done()

			except queue.Empty:

				if self.monitor.waitForAbort(0.1):
					self._stop()
					return

			except Exception as e:
				xbmc.log(f"gdrive error: {e}: {''.join(traceback.format_tb(e.__traceback__))}", xbmc.LOGERROR)
				self.task_done()


class LocalFileProcessor:

	def __init__(self, fileOperations, cache, syncRootPath, progressDialog=None):
		self.fileOperations = fileOperations
		self.cache = cache
		self.syncRootPath = syncRootPath
		self.progressDialog = progressDialog
		self.titleCacheManager = TitleCacheManager()

	def __enter__(self):
		return self

	def __exit__(self, excType, excValue, excTraceback):
		self.titleCacheManager.insertMovies()
		self.titleCacheManager.insertSeries()

	def processFiles(self, folder, folderSettings, threadCount):
		files = folder.files
		dirPath = folder.localPath
		videos = files.get("video")
		mediaAssets = files.get("media_asset")
		titleIdentifier = TitleIdentifier(getTMDBSettings(folderSettings))
		folderRenaming = folderSettings["folder_renaming"]
		fileRenaming = folderSettings["file_renaming"]

		if self.progressDialog:
			strm = files.get("strm")

			if strm:
				self.progressDialog.incrementFiles(len(strm))

		if videos:

			with ThreadPool(threadCount) as pool:
				[
					pool.submit(
						self._processVideo,
						file,
						dirPath,
						folderRenaming,
						fileRenaming,
						titleIdentifier,
					) for file in videos
				]

		if mediaAssets:

			with ThreadPool(threadCount) as pool:
				[
					pool.submit(
						self._processMediaAsset,
						file,
						dirPath,
						folderRenaming,
						fileRenaming,
						titleIdentifier,
					) for file in mediaAssets
				]

	def _processMediaAsset(self, file, dirPath, folderRenaming, fileRenaming, titleIdentifier):
		filename = file.localName
		remoteName = file.remoteName
		mediaType = file.media
		originalName = originalFolder = True

		if mediaType in ("movie", "episode"):
			newFilename = None
			modifiedName = file.formatName(self.titleCacheManager, titleIdentifier)

			if modifiedName:
				newFilename = modifiedName.get("filename")

			if newFilename:

				if fileRenaming:
					originalName = False
					fileExtension = f".{file.extension}"
					assetType = file.type

					if assetType == "subtitles":
						language = ""

						if file.language:
							language += f".{file.language}"

						if re.search("forced\.\w*$", remoteName, re.IGNORECASE):
							language += ".Forced"

						fileExtension = f"{language}{fileExtension}"

					elif assetType in ARTWORK:
						fileExtension = f"-{assetType}{fileExtension}"

					filename = f"{newFilename}{fileExtension}"

				if folderRenaming:
					originalFolder = False

					if mediaType == "movie":
						dirPath = os.path.join(self.syncRootPath, "[gDrive] Movies", newFilename)
					else:
						dirPath = os.path.join(
							self.syncRootPath,
							"[gDrive] Series",
							f"{modifiedName['title']} ({modifiedName['year']})",
							f"Season {file.season}",
						)

		filePath = self.fileOperations.renameFile(self.syncRootPath, file.localPath, dirPath, filename)

		if self.progressDialog:
			self.progressDialog.processRenamedFile(remoteName)

		data = {
			"local_path": filePath.replace(self.syncRootPath, "", 1) if not originalFolder else False,
			"local_name": os.path.basename(filePath),
			"original_name": originalName,
			"original_folder": originalFolder,
		}
		self.cache.updateFile(data, file.id)

	def _processVideo(self, file, dirPath, folderRenaming, fileRenaming, titleIdentifier):
		filename = f"{file.basename}.strm"
		mediaType = file.media
		originalName = originalFolder = True
		newFilename = None

		if mediaType in ("movie", "episode"):
			modifiedName = file.formatName(self.titleCacheManager, titleIdentifier)

			if modifiedName:
				newFilename = modifiedName.get("filename")

			if newFilename:

				if fileRenaming:
					filename = f"{newFilename}.strm"
					originalName = False

				if folderRenaming:
					originalFolder = False

					if mediaType == "movie":
						dirPath = os.path.join(self.syncRootPath, "[gDrive] Movies", newFilename)
					else:
						dirPath = os.path.join(
							self.syncRootPath,
							"[gDrive] Series",
							f"{modifiedName['title']} ({modifiedName['year']})",
							f"Season {file.season}",
						)

		filePath = self.fileOperations.renameFile(self.syncRootPath, file.localPath, dirPath, filename)
		localName = os.path.basename(filePath)

		if self.progressDialog:
			self.progressDialog.processRenamedFile(file.remoteName)

		if file.updateDB:
			dbEditor.processData(filePath, dirPath, localName)

		data = {
			"local_path": filePath.replace(self.syncRootPath, "", 1) if not originalFolder else False,
			"local_name": localName,
			"original_name": originalName,
			"original_folder": originalFolder,
		}
		self.cache.updateFile(data, file.id)

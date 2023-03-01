import os

from . import helpers
from .. import library


class FileProcessor:

	def __init__(self, cloudService, fileOperations, settings, cache):
		self.cloudService = cloudService
		self.fileOperations = fileOperations
		self.settings = settings
		self.cache = cache

	def processFiles(
		self,
		files,
		folderSettings,
		dirPath,
		syncRootPath,
		driveID,
		rootFolderID,
		parentFolderID,
	):
		syncRootPath = syncRootPath + os.sep
		videos = files.get("video")
		mediaAssets = files.get("media_assets")
		strm = files.get("strm")

		if videos:
			self.processVideos(
				videos,
				mediaAssets,
				folderSettings,
				dirPath,
				syncRootPath,
				driveID,
				rootFolderID,
				parentFolderID,
			)

		if strm:
			self.processSTRM(strm, dirPath, driveID, rootFolderID, parentFolderID)

		if mediaAssets:

			for assetName, assets in mediaAssets.items():

				if not assets:
					continue

				self.processMediaAssets(
					assets,
					syncRootPath,
					dirPath,
					None,
					True,
					True,
					driveID,
					rootFolderID,
					parentFolderID,
				)

			# file = {
				# "drive_id": driveID,
				# "file_id": fileID,
				# "local_path": False,
				# "parent_folder_id": parentFolderID,
				# "root_folder_id": rootFolderID,
				# "local_name": os.path.basename(filePath),
				# "remote_name": filename,
				# "original_name": True,
				# "original_folder": True,
			# }

	def processMediaAssets(
		self,
		mediaAssets,
		syncRootPath,
		dirPath,
		videoFilename,
		originalName,
		originalFolder,
		driveID,
		rootFolderID,
		parentFolderID,
	):

		for assetType, assets in list(mediaAssets.items()):

			for file in assets:
				filename = file.name

				if not originalName:

					if assetType == "subtitles":
						_, fileExtension = os.path.splitext(filename)
					elif assetType in ("poster", "fanart"):
						fileExtension = f"-{assetType}.jpg"

					filePath = helpers.generateFilePath(dirPath, f"{videoFilename}{fileExtension}")
				else:
					filePath = helpers.generateFilePath(dirPath, filename)

				fileID = file.id

				if file.encrypted:
					self.fileOperations.downloadFile(dirPath, filePath, fileID, encrypted=True)
				else:
					self.fileOperations.downloadFile(dirPath, filePath, fileID)

				file = {
					"file_id": fileID,
					"drive_id": driveID,
					"local_path": filePath.replace(syncRootPath, "") if not originalFolder else False,
					"parent_folder_id": parentFolderID,
					"root_folder_id": rootFolderID,
					"local_name": os.path.basename(filePath),
					"remote_name": filename,
					"original_name": originalName,
					"original_folder": originalFolder,
				}
				self.cache.addFile(file)

			del mediaAssets[assetType]

	def processSTRM(
		self,
		strm,
		dirPath,
		driveID,
		rootFolderID,
		parentFolderID,
	):

		for file in strm:
			fileID = file.id
			filename = file.name
			encrypted = file.encrypted
			filePath = helpers.generateFilePath(dirPath, filename)

			if encrypted:
				self.fileOperations.downloadFile(dirPath, filePath, fileID, encrypted=True)
			else:
				self.fileOperations.downloadFile(dirPath, filePath, fileID)

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
			self.cache.addFile(file)

	def processVideos(
		self,
		videos,
		mediaAssets,
		folderSettings,
		dirPath,
		syncRootPath,
		driveID,
		rootFolderID,
		parentFolderID,
	):
		videos.reverse()
		folderRestructure = folderSettings["folder_restructure"]
		fileRenaming = folderSettings["file_renaming"]

		for video in videos:
			filename = video.name
			basename = video.basename
			ptnName = video.ptn_name
			fileID = video.id
			strmContent = helpers.createSTRMContents(driveID, fileID, video.encrypted, video.contents)
			newFilename = strmPath = False
			originalName = originalFolder = True

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
								f"{newFilename}.strm",
							)
							originalName = False
						else:
							strmPath = helpers.generateFilePath(
								dirPath,
								f"{basename}.strm",
							)

					elif str(video) == "Episode":
						dirPath = os.path.join(
							syncRootPath,
							"[gDrive] Series",
							modifiedName["title"],
							f"Season {video.season}",
						)

						if fileRenaming:
							strmPath = helpers.generateFilePath(dirPath, f"{newFilename}.strm")
							originalName = False
						else:
							strmPath = helpers.generateFilePath(dirPath, f"{basename}.strm")

					originalFolder = False

				elif fileRenaming and newFilename:
					strmPath = helpers.generateFilePath(dirPath, f"{newFilename}.strm")
					originalName = False

			if ptnName in mediaAssets:
				self.processMediaAssets(
					mediaAssets[ptnName],
					syncRootPath,
					dirPath,
					newFilename,
					originalName,
					originalFolder,
					driveID,
					rootFolderID,
					parentFolderID,
				)

			if not strmPath:
				strmPath = helpers.generateFilePath(dirPath, f"{basename}.strm")

			self.fileOperations.createFile(dirPath, strmPath, strmContent, mode="w+")

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
			self.cache.addFile(file)


def addFileToCache(file, fileID, fileIDs, cachedFiles):
	cachedFiles[fileID] = file
	fileIDs.append(fileID)

def removeFileFromCache(fileID, fileIDs, cachedFiles):

	if fileID in cachedFiles:
		del cachedFiles[fileID]

	if fileID in fileIDs:
		fileIDs.remove(fileID)

def removeCachedFiles(fileIDs, cachedFiles):

	for fileID in list(fileIDs):

		if fileID in cachedFiles:
			del cachedFiles[fileID]

	if fileID in fileIDs:
		fileIDs.remove(fileID)

def addDirectoryToCache(folderID, parentFolderID, directory, cachedDirectories):

	if parentFolderID in cachedDirectories:
		folderIDs = cachedDirectories[parentFolderID]["folder_ids"]

		if folderID not in folderIDs:
			folderIDs.append(folderID)

	cachedDirectories[folderID] = directory

def removeDirectoryFromCache(folderID, parentFolderID, cachedDirectories):

	if parentFolderID in cachedDirectories:
		folderIDs = cachedDirectories[parentFolderID]["folder_ids"]

		if folderID in folderIDs:
			folderIDs.remove(folderID)

	if folderID in cachedDirectories:
		del cachedDirectories[folderID]

def updateCachedPaths(oldPath, newPath, folderIDs, cachedDirectories):

	for folderID in folderIDs:
		cachedDirectory = cachedDirectories[folderID]
		cachedDirPath = cachedDirectory["local_path"]
		folderIDs = cachedDirectory["folder_ids"]
		modifiedPath = cachedDirPath.replace(oldPath, newPath)
		cachedDirectory["local_path"] = modifiedPath
		updateCachedPaths(oldPath, newPath, folderIDs, cachedDirectories)

def updateCache(cachedDirectories, cachedFiles, folderID):
	cachedDirectory = cachedDirectories[folderID]
	folderIDs = cachedDirectory["folder_ids"]
	fileIDs = cachedDirectory["file_ids"]
	removeCachedFiles(fileIDs, cachedFiles)
	updateCachedPaths(cachedDirectories, cachedFiles, folderIDs)
	del cachedDirectories[folderID]

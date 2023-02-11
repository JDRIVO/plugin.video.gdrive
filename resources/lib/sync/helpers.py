
def removeFolderIDfromCachedList(cachedDirectories, parentFolderID, folderID):

	if parentFolderID in cachedDirectories:
		folderIDs = cachedDirectories[parentFolderID]["folder_ids"]

		if folderID in folderIDs:
			folderIDs.remove(folderID)

def addFolderIDtoCachedList(cachedDirectories, parentFolderID, folderID):

	if parentFolderID in cachedDirectories:
		folderIDs = cachedDirectories[parentFolderID]["folder_ids"]

		if folderID not in folderIDs:
			folderIDs.append(folderID)

def removeFileIDfromCachedList(cachedDirectories, parentFolderID, fileID):

	if parentFolderID in cachedDirectories:
		fileIDs = cachedDirectories[parentFolderID]["file_ids"]

		if fileID in fileIDs:
			fileIDs.remove(fileID)

def addFileIDtoCachedList(cachedDirectories, parentFolderID, fileID):

	if parentFolderID in cachedDirectories:
		fileIDs = cachedDirectories[parentFolderID]["file_ids"]

		if fileID not in fileIDs:
			fileIDs.append(fileID)

def removeCachedFiles(fileIDs, cachedFiles):

	for fileID in list(fileIDs):

		if fileID in cachedFiles:
			del cachedFiles[fileID]

		fileIDs.remove(fileID)

def updateCache(cachedDirectories, cachedFiles, folderID):
	cachedDirectory = cachedDirectories[folderID]
	folderIDs = cachedDirectory["folder_ids"]
	fileIDs = cachedDirectory["file_ids"]
	removeCachedFiles(fileIDs, cachedFiles)

	for folderID in folderIDs:
		updateCachedPaths(cachedDirectories, cachedFiles, folderID)

	del cachedDirectories[folderID]

def updateCachedPaths(oldPath, newPath, cachedDirectories, folderID):
	cachedDirectory = cachedDirectories[folderID]
	cachedDirPath = cachedDirectory["local_path"]
	folderIDs = cachedDirectory["folder_ids"]

	# if oldPath in cachedDirPath:
		# replacement = cachedDirPath.replace(oldPath, newPath)
		# cachedDirectories[folderID][0] = replacement

	modifiedPath = cachedDirPath.replace(oldPath, newPath)
	cachedDirectory["local_path"] = modifiedPath

	for folderID in folderIDs:
		updateCachedPaths(oldPath, newPath, cachedDirectories, folderID)

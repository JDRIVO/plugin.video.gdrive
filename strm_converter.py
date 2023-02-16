import os

# Converts the old STRM format to the new format

oldStrmPath = ""
newStrmPath = ""
driveID = "" # Optional - if not included you will need to manually set the playback account in settings

for root, dirs, files in os.walk(oldStrmPath, topdown=False):

	for name in files:
		fileExt = name.rsplit(".", 1)[-1]

		if fileExt != "strm":
			continue

		newDirectory = root.replace(oldStrmPath, newStrmPath)
		newPath = os.path.join(newDirectory, name)
		oldPath = os.path.join(root, name)
		stInfo = os.stat(oldPath)

		if not os.path.isdir(newDirectory):
			os.makedirs(newDirectory)

		with open(newPath, "w") as newStrm:

			with open(oldPath, "r") as oldStrm:
				contents = oldStrm.read()
				contents = contents.replace("&filename=", "&file_id=")
				contents = contents.replace("&encfs=", "&encrypted=")
				if driveID: contents += f"&drive_id={driveID}"

			newStrm.write(contents)

		os.utime(newPath, (stInfo.st_atime, stInfo.st_mtime))

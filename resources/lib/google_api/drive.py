import os
import re
import datetime
import urllib.parse

from .. import network
from .. import encryption
from .. import filesystem

API_VERSION = "3"
GDRIVE_URL = "https://www.googleapis.com/drive/v3"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE_URL = "https://www.googleapis.com/auth/drive.readonly"

API = {
	"changes": GDRIVE_URL + "/changes",
	"drives": GDRIVE_URL + "/drives",
	"files": GDRIVE_URL + "/files",
}


class GoogleDrive:

	def __init__(self, accountManager):
		self.accountManager = accountManager

	def setAccount(self, account):
		self.account = account

	@staticmethod
	def getDownloadURL(fileID):
		params = {
			"supportsAllDrives": "true",
			"alt": "media",
		}
		return network.helpers.addQueryString(network.helpers.mergePaths(API["files"], fileID), params)

	def refreshToken(self):
		key = self.account.key

		if key:
			jwt = encryption.json_web_token.JsonWebToken(self.account.email, key, SCOPE_URL, GOOGLE_TOKEN_URL).create()
			data = {
				"assertion": jwt,
				"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
			}
		else:
			data = {
				"client_id": self.account.clientID,
				"client_secret": self.account.clientSecret,
				"refresh_token": self.account.refreshToken,
				"grant_type": "refresh_token",
			}
		response = network.requester.sendPayload(GOOGLE_TOKEN_URL, data, method="POST")

		if "failed" in response:
			return "failed"

		response["access_token"].rstrip(".")
		self.account.accessToken = response["access_token"].rstrip(".")
		expiry = datetime.datetime.now() + datetime.timedelta(seconds=response["expires_in"] - 600)
		self.account.expiry = expiry

	def getHeaders(self, accessToken=None, additionalHeader=None, additionalValue=None):
		cookie = self.account.driveStream
		accessToken = self.account.accessToken
		if not accessToken: accessToken = ""
		if not cookie: cookie = ""

		if additionalHeader:
			return {
				"Cookie": "DRIVE_STREAM=" + cookie,
				"Authorization": "Bearer " + accessToken,
				additionalHeader: additionalValue,
			}
		else:
			return {
				"Cookie": "DRIVE_STREAM=" + cookie,
				"Authorization": "Bearer " + accessToken,
			}

	def getHeadersEncoded(self):
		return urllib.parse.urlencode(self.getHeaders())

	def getStreams(self, fileID, resolutionPriority=None):
		url = "https://drive.google.com/get_video_info?docid=" + fileID
		self.account.driveStream = None
		responseData, cookie = network.requester.sendPayload(url, headers=self.getHeaders(), cookie=True)
		self.account.driveStream = re.findall("DRIVE_STREAM=(.*?);", cookie)[0]

		for _ in range(5):
			responseData = urllib.parse.unquote(responseData)

		# urls = re.sub("\\\\u003d", "=", urls)
		# urls = re.sub("\\\\u0026", "&", urls)
		urls = re.sub("\&url\=https://", "\@", responseData)
		streams = {}
		resolutions = {}
		resolutionList = ["360", "480", "720", "1080"]

		for r in re.finditer("([\d]+)/[\d]+x([\d]+)", urls, re.DOTALL):
			itag, resolution = r.groups()

			if resolution not in resolutionList:
				resolutionInt = int(resolution)

				if resolutionInt < 360:
					resolution = "360"
				elif resolutionInt > 360 and resolutionInt < 480:
					resolution = "480"
				elif resolutionInt > 480 and resolutionInt < 720:
					resolution = "720"
				elif resolutionInt > 720:
					resolution = "1080"

			resolution = resolution + "P"
			resolutions[resolution] = itag
			streams[itag] = {"resolution": resolution}

		for r in re.finditer("\@([^\@]+)", urls):
			videoURL = r.group(1)
			itag = re.findall("itag=([\d]+)", videoURL)[0]
			streams[itag]["url"] = "https://" + videoURL + "|" + self.getHeadersEncoded()

		if streams and resolutionPriority:

			for resolution in resolutionPriority:

				if resolution == "Original":
					return
				elif resolution in resolutions:
					return resolution, streams[resolutions[resolution]]["url"]

		elif streams:
			return sorted([(v["resolution"], v["url"]) for k, v in streams.items()], key=lambda x: int(x[0][:-1]), reverse=True)

	def getDrives(self):
		params = {"pageSize": "100"}
		drives = []
		pageToken = True

		while pageToken:
			url = network.helpers.addQueryString(API["drives"], params)
			response = network.requester.sendPayload(url, headers=self.getHeaders())

			pageToken = response.get("nextPageToken")

			if not pageToken:
				drives += response["drives"]
				return drives
			else:
				drives += response["drives"]
				params["pageToken"] = pageToken

	def getDriveID(self):
		url = network.helpers.mergePaths(API["files"], "root")
		response = network.requester.sendPayload(url, headers=self.getHeaders())

		if "failed" in response:
			return response

		return response.get("id")

	def downloadFile(self, fileID):
		params = {"alt": "media"}
		url = network.helpers.addQueryString(network.helpers.mergePaths(API["files"], fileID), params)
		file = network.requester.sendPayload(url, headers=self.getHeaders(), download=True)

		if file:
			return file

	def getParentDirectoryID(self, fileID):
		params = {
			"fields": "parents,name",
			"supportsAllDrives": "true",
			"includeItemsFromAllDrives": "true",
		}
		url = network.helpers.addQueryString(network.helpers.mergePaths(API["files"], fileID), params)
		response = network.requester.sendPayload(url, headers=self.getHeaders())
		return response["parents"][0]

	def getDirectory(self, cache, folderID):
		dirPath = ""
		cachedDirectory = None
		cachedFolder = None

		while not cachedDirectory and not cachedFolder:

			params = {
				"fields": "parents,name",
				"supportsAllDrives": "true",
				"includeItemsFromAllDrives": "true",
			}
			url = network.helpers.addQueryString(network.helpers.mergePaths(API["files"], folderID), params)
			response = network.requester.sendPayload(url, headers=self.getHeaders())

			try:
				dirName, folderID = response["name"], response["parents"][0]
			except Exception:
				return None, None

			dirName = filesystem.helpers.removeProhibitedFSchars(dirName)
			dirPath = os.path.join(dirName, dirPath)
			cachedDirectory = cache.getDirectory(folderID)
			cachedFolder = cache.getFolder(folderID)

		if cachedDirectory:
			rootFolderID = cachedDirectory["root_folder_id"]
			dirPath = os.path.join(cachedDirectory["local_path"], dirPath).rstrip(os.sep)
			return dirPath, rootFolderID
		elif cachedFolder:
			rootFolderID = folderID
			dirPath = os.path.join(cachedFolder["local_path"], dirPath).rstrip(os.sep)
			return dirPath, rootFolderID

	def listDirectory(self, folderID="root", sharedWithMe=False, foldersOnly=False, starred=False, search=False):
		params = {}

		if foldersOnly:

			if sharedWithMe:
				params["q"] = "mimeType='application/vnd.google-apps.folder' and sharedWithMe=true and not trashed"
			elif starred:
				params["q"] = "mimeType='application/vnd.google-apps.folder' and starred and not trashed"
			elif search:
				params["q"] = f"mimeType='application/vnd.google-apps.folder' and name contains '{search}' and not trashed"
			else:
				params["q"] = f"mimeType='application/vnd.google-apps.folder' and '{folderID}' in parents and not trashed"

			params["fields"] = "nextPageToken,files(id,name)"

		else:
			params.update(
				{
					"q": f"'{folderID}' in parents and not trashed",
					"fields": "nextPageToken,files(id,parents,name,mimeType,videoMediaMetadata,fileExtension)",
				}
			)
		params.update(
			{
				"supportsAllDrives": "true",
				"includeItemsFromAllDrives": "true",
				"pageSize": "1000",
			}
		)
		files = []
		pageToken = True

		while pageToken:
			url = network.helpers.addQueryString(API["files"], params)
			response = network.requester.sendPayload(url, headers=self.getHeaders())
			pageToken = response.get("nextPageToken")

			if not pageToken:
				files += response["files"]
				return files
			else:
				files += response["files"]
				params["pageToken"] = pageToken

	def getPageToken(self):
		params = {"supportsAllDrives": "true"}
		url = network.helpers.addQueryString(network.helpers.mergePaths(API["changes"], "startPageToken"), params)
		response = network.requester.sendPayload(url, headers=self.getHeaders())
		return response.get("startPageToken")

	def getChanges(self, pageToken):
		params = {
			"pageToken": pageToken,
			"fields": "nextPageToken,newStartPageToken,changes(file(id,name,parents,trashed,mimeType,fileExtension,videoMediaMetadata))",
			"supportsAllDrives": "true",
			"includeItemsFromAllDrives": "true",
			"pageSize": "1000",
		}
		changes = []
		nextPageToken = True

		while nextPageToken:
			url = network.helpers.addQueryString(API["changes"], params)
			response = network.requester.sendPayload(url, headers=self.getHeaders())
			nextPageToken = response.get("nextPageToken")

			if not nextPageToken:
				changes += response["changes"]
				return changes, response["newStartPageToken"]
			else:
				changes += response["changes"]
				params["pageToken"] = nextPageToken

	def getAuthURL(self, clientID, port):
		params = {
			"client_id": clientID,
			"redirect_uri": "http://localhost:" + str(port) + "/status",
			"response_type": "code",
			"scope": SCOPE_URL,
			"access_type": "offline",
			"prompt": "consent",

		}
		return network.helpers.addQueryString(GOOGLE_AUTH_URL, params)

	def getToken(self, clientID, clientSecret, code, port):
		data = {
			"client_id": clientID,
			"client_secret": clientSecret,
			"code": code,
			"grant_type": "authorization_code",
			"redirect_uri": "http://localhost:" + str(port) + "/status",
		}
		return network.requester.sendPayload(GOOGLE_TOKEN_URL, data, method="POST")

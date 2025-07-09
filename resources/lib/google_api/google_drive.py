import os
import re
import datetime

from ..network import http_requester
from ..network.network_helpers import addQueryString, mergePaths, parseQuery, unquote
from ..encryption.jwt import JsonWebToken
from ..filesystem.fs_helpers import removeProhibitedFSchars

API_VERSION = "3"
GDRIVE_URL = "https://www.googleapis.com/drive/v3"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE_URL = "https://www.googleapis.com/auth/drive.readonly"

API = {
	"changes": f"{GDRIVE_URL}/changes",
	"drives": f"{GDRIVE_URL}/drives",
	"files": f"{GDRIVE_URL}/files",
}


class GoogleDrive:

	def __init__(self):
		self.account = None

	def downloadFile(self, fileID):
		params = {"alt": "media"}
		url = addQueryString(mergePaths(API["files"], fileID), params)
		return http_requester.request(url, headers=self.getHeaders(), raw=True)

	def getAuthURL(self, clientID, port):
		params = {
			"client_id": clientID,
			"redirect_uri": f"http://localhost:{port}/status",
			"response_type": "code",
			"scope": SCOPE_URL,
			"access_type": "offline",
			"prompt": "consent",
		}
		return addQueryString(GOOGLE_AUTH_URL, params)

	def getChanges(self, pageToken):

		if not pageToken:
			pageToken = self.getPageToken()

		params = {
			"pageToken": pageToken,
			"fields": "nextPageToken,newStartPageToken,changes(fileId,changeType,removed,file(name,parents,trashed,mimeType,fileExtension,videoMediaMetadata,modifiedTime))",
			"supportsAllDrives": "true",
			"includeItemsFromAllDrives": "true",
			"pageSize": "1000",
		}
		changes = []
		pageToken = True

		while pageToken:
			url = addQueryString(API["changes"], params)
			response = http_requester.request(url, headers=self.getHeaders())
			pageToken = response.get("nextPageToken")
			changes += response.get("changes")
			params["pageToken"] = pageToken

		return changes, response.get("newStartPageToken")

	def getDirectory(self, cache, folderID, encryptor, excludedIDs):
		params = {
			"fields": "parents,name",
			"supportsAllDrives": "true",
			"includeItemsFromAllDrives": "true",
		}
		dirs, folderIDs = [], []

		while True:

			if folderID in excludedIDs:
				excludedIDs += folderIDs
				return None, None

			folderIDs.append(folderID)
			cachedDirectory = cache.getDirectory({"folder_id": folderID})
			cachedFolder = cache.getFolder({"folder_id": folderID})

			if cachedDirectory or cachedFolder:
				break

			url = addQueryString(mergePaths(API["files"], folderID), params)
			response = http_requester.request(url, headers=self.getHeaders())

			try:
				dirName, folderID = response["name"], response["parents"][0]
			except KeyError:
				excludedIDs += folderIDs
				return None, None

			dirs.insert(0, dirName)

		if cachedDirectory:
			rootFolderID = cachedDirectory["root_folder_id"]
			basePath = cachedDirectory["local_path"]
			encryptionID = cache.getFolder({"folder_id": rootFolderID})["encryption_id"]
		else:
			rootFolderID = folderID
			basePath = cachedFolder["local_path"]
			encryptionID = cachedFolder["encryption_id"]

		encryptorSet = encryptor.setEncryptor(encryptionID) if encryptionID else False

		if encryptorSet:
			dirs = [removeProhibitedFSchars(encryptor.decryptDirName(d)) for d in dirs]
		else:
			dirs = [removeProhibitedFSchars(d) for d in dirs]

		dirPath = os.path.join(basePath, *dirs).rstrip(os.sep)
		return dirPath, rootFolderID

	@staticmethod
	def getDownloadURL(fileID):
		params = {
			"supportsAllDrives": "true",
			"alt": "media",
		}
		return addQueryString(mergePaths(API["files"], fileID), params)

	def getDriveID(self):
		url = mergePaths(API["files"], "root")

		if response := http_requester.request(url, headers=self.getHeaders()):
			return response.get("id")

	def getDrives(self):
		params = {"pageSize": "100"}
		drives = []
		pageToken = True

		while pageToken:
			url = addQueryString(API["drives"], params)
			response = http_requester.request(url, headers=self.getHeaders())
			pageToken = response.get("nextPageToken")
			drives += response.get("drives")
			params["pageToken"] = pageToken

		return drives

	def getHeaders(self):
		return {"Authorization": f"Bearer {self.account.accessToken or ''}"}

	def getPageToken(self):
		params = {"supportsAllDrives": "true"}
		url = addQueryString(mergePaths(API["changes"], "startPageToken"), params)
		response = http_requester.request(url, headers=self.getHeaders())
		return response.get("startPageToken")

	def getParentDirectoryID(self, fileID):
		params = {
			"fields": "parents,name",
			"supportsAllDrives": "true",
			"includeItemsFromAllDrives": "true",
		}
		url = addQueryString(mergePaths(API["files"], fileID), params)
		response = http_requester.request(url, headers=self.getHeaders())

		if id := response.get("parents"):
			return id[0]

	def getStreams(self, fileID, resolutionPriority=None):
		url = f"https://drive.google.com/get_video_info?docid={fileID}"
		response = http_requester.request(url, headers=self.getHeaders())
		parsedData = parseQuery(response)
		formats = parsedData.get("fmt_list")

		if not formats:
			return

		streamMap = parsedData.get("fmt_stream_map")
		streams, resolutionMap = {}, {}
		resolutions = [1080, 720, 480, 360]

		for match in re.finditer("(\d+)/(\d+)x(\d+)", formats):
			itag, r1, r2 = match.groups()
			resolution = min(int(r1), int(r2))
			resolution = min(resolutions, key=lambda x: abs(x - resolution))
			resolution = f"{resolution}P"
			resolutionMap[resolution] = itag
			streams[itag] = {"resolution": resolution}

		for match in re.finditer(r"(\d+)\|(https://[^,]+)", streamMap):
			itag, url = match.groups()
			streams[itag]["url"] = url

		if streams:

			if resolutionPriority:

				for resolution in resolutionPriority:

					if resolution == "Original":
						return

					itag = resolutionMap.get(resolution)

					if itag and "url" in streams[itag]:
						return resolution, streams[itag]["url"]

			return {"Original": None, **{v["resolution"]: v["url"] for v in streams.values()}}

	def getToken(self, clientID, clientSecret, code, port):
		data = {
			"client_id": clientID,
			"client_secret": clientSecret,
			"code": code,
			"grant_type": "authorization_code",
			"redirect_uri": f"http://localhost:{port}/status",
		}
		return http_requester.request(GOOGLE_TOKEN_URL, data)

	def listDirectory(self, folderID="root", sharedWithMe=False, starred=False, searchQuery=None, customQuery=None):
		params = {
			"supportsAllDrives": "true",
			"includeItemsFromAllDrives": "true",
			"pageSize": "1000",
		}

		if customQuery:
			params["q"] = customQuery
			params["fields"] = "nextPageToken,files(id,parents,name,mimeType,videoMediaMetadata,fileExtension,modifiedTime)"
		else:

			if sharedWithMe:
				params["q"] = "mimeType='application/vnd.google-apps.folder' and sharedWithMe=true and not trashed"
			elif starred:
				params["q"] = "mimeType='application/vnd.google-apps.folder' and starred and not trashed"
			elif searchQuery:
				params["q"] = f"mimeType='application/vnd.google-apps.folder' and name contains '{searchQuery}' and not trashed"
			else:
				params["q"] = f"mimeType='application/vnd.google-apps.folder' and '{folderID}' in parents and not trashed"

			params["fields"] = "nextPageToken,files(id,name,modifiedTime)"

		items = []
		pageToken = True

		while pageToken:
			url = addQueryString(API["files"], params)
			response = http_requester.request(url, headers=self.getHeaders())
			pageToken = response.get("nextPageToken")
			items += response.get("files")
			params["pageToken"] = pageToken

		return items

	def refreshToken(self):

		if self.account.type == "oauth":
			data = {
				"client_id": self.account.clientID,
				"client_secret": self.account.clientSecret,
				"refresh_token": self.account.refreshToken,
				"grant_type": "refresh_token",
			}
		else:
			jwt = JsonWebToken(self.account.email, self.account.key, SCOPE_URL, GOOGLE_TOKEN_URL)
			data = {
				"assertion": jwt.create(),
				"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
			}

		if response := http_requester.request(GOOGLE_TOKEN_URL, data):
			self.account.accessToken = response["access_token"].rstrip(".")
			expiry = datetime.datetime.now() + datetime.timedelta(seconds=response["expires_in"] - 600)
			self.account.tokenExpiry = expiry
			return True

	def setAccount(self, account):
		self.account = account

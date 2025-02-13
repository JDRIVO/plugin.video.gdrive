import os
import re
import datetime
import urllib.parse

from ..network import http_requester
from ..network.network_helpers import addQueryString, mergePaths
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
			"fields": "nextPageToken,newStartPageToken,changes(file(id,name,parents,trashed,mimeType,fileExtension,videoMediaMetadata,modifiedTime))",
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

	def getDirectory(self, cache, folderID):
		dirPath = ""
		cachedDirectory = None
		cachedFolder = cache.getFolder({"folder_id": folderID})
		params = {
			"fields": "parents,name",
			"supportsAllDrives": "true",
			"includeItemsFromAllDrives": "true",
		}

		while not cachedDirectory and not cachedFolder:
			url = addQueryString(mergePaths(API["files"], folderID), params)
			response = http_requester.request(url, headers=self.getHeaders())

			try:
				dirName, folderID = response["name"], response["parents"][0]
			except KeyError:
				return None, None

			dirName = removeProhibitedFSchars(dirName)
			dirPath = os.path.join(dirName, dirPath)
			cachedDirectory = cache.getDirectory({"folder_id": folderID})
			cachedFolder = cache.getFolder({"folder_id": folderID})

		if cachedDirectory:
			rootFolderID = cachedDirectory["root_folder_id"]
			dirPath = os.path.join(cachedDirectory["local_path"], dirPath).rstrip(os.sep)
			return dirPath, rootFolderID
		elif cachedFolder:
			rootFolderID = folderID
			dirPath = os.path.join(cachedFolder["local_path"], dirPath).rstrip(os.sep)
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
		response = http_requester.request(url, headers=self.getHeaders())

		if response:
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
		return {
			"Cookie": f"DRIVE_STREAM={self.account.driveStream or ''}",
			"Authorization": f"Bearer {self.account.accessToken or ''}",
		}

	def getHeadersEncoded(self):
		return urllib.parse.urlencode(self.getHeaders())

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
		id = response.get("parents")

		if id:
			return id[0]

	def getStreams(self, fileID, resolutionPriority=None):
		url = f"https://drive.google.com/get_video_info?docid={fileID}"
		self.account.driveStream = None
		responseData, cookie = http_requester.request(url, headers=self.getHeaders(), cookie=True)
		self.account.driveStream = re.search("DRIVE_STREAM=(.*?);", cookie).group(1)

		for _ in range(5):
			responseData = urllib.parse.unquote(responseData)

		urls = re.sub("\&url\=https://", "\@", responseData)
		streams, resolutionMap = {}, {}
		resolutions = [1080, 720, 480, 360]

		for r in re.finditer("([\d]+)/([\d]+)x([\d]+)", urls, re.DOTALL):
			itag, r1, r2 = r.groups()
			resolution = min(int(r1), int(r2))

			if resolution not in resolutions:

				if resolution >= 1080:
					resolution = 1080
				elif resolution >= 720:
					resolution = 720
				elif resolution >= 480:
					resolution = 480
				else:
					resolution = 360

			resolution = f"{resolution}P"
			resolutionMap[resolution] = itag
			streams[itag] = {"resolution": resolution}

		for r in re.finditer("\@([^\@;]+)", urls):
			videoURL = r.group(1)
			itag = re.search("itag=([\d]+)", videoURL).group(1)
			streams[itag]["url"] = f"https://{videoURL}|{self.getHeadersEncoded()}"

		if streams and resolutionPriority:

			for resolution in resolutionPriority:

				if resolution == "Original":
					return
				elif resolution in resolutionMap:
					return resolution, streams[resolutionMap[resolution]]["url"]

		elif streams:
			return {"Original": None, **{v["resolution"]: v["url"] for k, v in streams.items()}}

	def getToken(self, clientID, clientSecret, code, port):
		data = {
			"client_id": clientID,
			"client_secret": clientSecret,
			"code": code,
			"grant_type": "authorization_code",
			"redirect_uri": f"http://localhost:{port}/status",
		}
		return http_requester.request(GOOGLE_TOKEN_URL, data, method="POST")

	def listDirectory(self, folderID="root", sharedWithMe=False, foldersOnly=False, starred=False, search=False, customQuery=False):
		params = {
			"supportsAllDrives": "true",
			"includeItemsFromAllDrives": "true",
			"pageSize": "1000",
		}

		if customQuery:
			params["q"] = customQuery
			params["fields"] = "nextPageToken,files(id,parents,name,mimeType,videoMediaMetadata,fileExtension,modifiedTime)"
		elif foldersOnly:

			if sharedWithMe:
				params["q"] = "mimeType='application/vnd.google-apps.folder' and sharedWithMe=true and not trashed"
			elif starred:
				params["q"] = "mimeType='application/vnd.google-apps.folder' and starred and not trashed"
			elif search:
				params["q"] = f"mimeType='application/vnd.google-apps.folder' and name contains '{search}' and not trashed"
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
		key = self.account.key

		if key:
			jwt = JsonWebToken(self.account.email, key, SCOPE_URL, GOOGLE_TOKEN_URL).create()
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

		response = http_requester.request(GOOGLE_TOKEN_URL, data, method="POST")

		if not response:
			return

		self.account.accessToken = response["access_token"].rstrip(".")
		expiry = datetime.datetime.now() + datetime.timedelta(seconds=response["expires_in"] - 600)
		self.account.expiry = expiry
		return True

	def setAccount(self, account):
		self.account = account

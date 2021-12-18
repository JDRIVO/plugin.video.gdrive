import re
import urllib.error
import urllib.parse
import urllib.request
import xbmc
from resources.lib import encryption

API_VERSION = "3"
GOOGLE_AUTH_URL = "https://oauth2.googleapis.com/token"
SCOPE_URL = "https://www.googleapis.com/auth/drive.readonly"
GDRIVE_URL = "https://www.googleapis.com/drive/v3/files/"
GDRIVE_PARAMS = "?supportsAllDrives=true&alt=media"


class GoogleDrive:

	def __init__(self, settings, accountManager, userAgent):
		self.settings = settings
		self.accountManager = accountManager
		self.userAgent = userAgent

	def setAccount(self, account):
		self.account = account

	def constructDriveURL(self):
		return GDRIVE_URL + self.settings.getParameter("filename") + GDRIVE_PARAMS

	def getToken(self, code, clientID, clientSecret):
		header = {"User-Agent": self.userAgent, "Content-Type": "application/x-www-form-urlencoded"}
		data = "code={}&client_id={}&client_secret={}&redirect_uri=urn:ietf:wg:oauth:2.0:oob&grant_type=authorization_code".format(
			code, clientID, clientSecret
		)
		req = urllib.request.Request(GOOGLE_AUTH_URL, data.encode("utf-8"), header)

		try:
			response = urllib.request.urlopen(req)
		except urllib.error.URLError as e:
			return "failed", str(e)

		responseData = response.read().decode("utf-8")
		response.close()
		error = re.findall('"error_description": "(.*?)"', responseData)

		if error:
			return "failed", error[0]

		return re.findall('"refresh_token": "(.*?)"', responseData, re.DOTALL)[0]

	def refreshToken(self):
		header = {"User-Agent": self.userAgent, "Content-Type": "application/x-www-form-urlencoded"}
		key = self.account.get("key")

		if key:
			jwt = encryption.JasonWebToken(self.account["email"], key, SCOPE_URL, GOOGLE_AUTH_URL).create()
			data = "grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=" + jwt
		else:
			data = "client_id={}&client_secret={}&refresh_token={}&grant_type=refresh_token".format(
				self.account["client_id"], self.account["client_secret"], self.account["refresh_token"]
			)

		req = urllib.request.Request(GOOGLE_AUTH_URL, data.encode("utf-8"), header)

		try:
			response = urllib.request.urlopen(req)
		except urllib.error.URLError as e:
			xbmc.log(self.settings.getLocalizedString(30003) + ": " + str(e))
			return "failed"

		responseData = response.read().decode("utf-8")
		response.close()
		error = re.findall('"error_description": "(.*?)"', responseData)

		if error:
			xbmc.log(self.settings.getLocalizedString(30003) + ": " + error[0])
			return "failed"

		if key:
			accessToken = re.findall('"access_token":"(.*?)[.]*"', responseData)[0]
		else:
			accessToken = re.findall('"access_token": "(.*?)"', responseData)[0]

		self.account["access_token"] = accessToken

	def getHeaders(self, additionalHeader=None, additionalValue=None):
		accessToken = str(self.account.get("access_token"))

		if additionalHeader:
			return {"Authorization": "Bearer " + accessToken, additionalHeader: additionalValue}
		else:
			return {"Authorization": "Bearer " + accessToken}

	def getHeadersEncoded(self):
		return urllib.parse.urlencode(self.getHeaders())

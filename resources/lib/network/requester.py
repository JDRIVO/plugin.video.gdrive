import json
import urllib.error
import urllib.parse
import urllib.request

import xbmc

USER_AGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.38 Safari/532.0"

HEADERS = {
	"User-Agent": USER_AGENT,
}

HEADERS_FORM_ENCODED = {
	"User-Agent": USER_AGENT,
	"Content-Type": "application/x-www-form-urlencoded",
}


def makeRequest(url, data=None, headers=HEADERS, cookie=None, download=False, method="GET"):

	if method == "POST":
		headers = HEADERS_FORM_ENCODED

	if data:
		data = urllib.parse.urlencode(data).encode("utf8")

	req = urllib.request.Request(url, data, headers)

	try:
		response = urllib.request.urlopen(req)
	except urllib.error.URLError as e:
		xbmc.log("gdrive error: " + str(e))
		return

	if download:
		return response

	responseData = response.read().decode("utf-8")

	if cookie:
		cookie = response.headers["set-cookie"]

	response.close()

	try:
		responseData = json.loads(responseData)
	except Exception:
		pass

	if not cookie:
		return responseData
	else:
		return responseData, cookie

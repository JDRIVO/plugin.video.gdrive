import json
from urllib.error import URLError
from urllib.request import Request, urlopen

import xbmc

USER_AGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.38 Safari/532.0"
HEADERS = {"User-Agent": USER_AGENT}
HEADERS_JSON_ENCODED = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}


def request(url, data=None, headers=HEADERS, cookie=False, raw=False, method="GET"):

	if method == "POST":
		headers = HEADERS_JSON_ENCODED

	if data:
		data = json.dumps(data).encode("utf-8")

	attempts = 3
	request = Request(url, data, headers)

	for attempt in range(attempts):

		try:

			response = urlopen(request)

			if raw:
				return response

			data = response.read().decode("utf-8")
			response.close()
			break

		except URLError as e:
			attempts -= 1

			if not attempts:
				xbmc.log(f"gdrive error: {e}", xbmc.LOGERROR)
				return {}

			xbmc.sleep(1000)

	if cookie:
		cookie = response.headers["set-cookie"]

	try:
		data = json.loads(data)
	except json.JSONDecodeError:
		pass

	if not cookie:
		return data
	else:
		return data, cookie

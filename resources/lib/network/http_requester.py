import json
import urllib3

import xbmc

USER_AGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.38 Safari/532.0"
HEADERS = {"User-Agent": USER_AGENT}
HTTP = urllib3.PoolManager()


def request(url, data=None, headers=HEADERS, cookie=False, raw=False, method="GET"):

	if data:
		method = "POST"

	attempts = 3

	for attempt in range(attempts):

		try:
			response = HTTP.request(method, url, headers=headers, json=data)

			if raw:
				return response.data

			data = response.data.decode("utf-8")
			break

		except urllib3.exceptions.HTTPError as e:
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

	return data if not cookie else (data, cookie)

import json

import xbmc
import urllib3

USER_AGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.38 Safari/532.0"
HEADERS = {"User-Agent": USER_AGENT}
HTTP = urllib3.PoolManager()


def request(url, data=None, headers=HEADERS, raw=False, method="GET"):

	if data:
		method = "POST"

	for attempt in range(3):

		try:
			response = HTTP.request(method, url, headers=headers, json=data, preload_content=not raw)

			if response.status >= 400:

				try:
					error = json.loads(response.data.decode("utf-8"))
					raise urllib3.exceptions.HTTPError(f"Status: {response.status}, Reason: {response.reason}, Error details: {error}")
				except json.JSONDecodeError:
					raise urllib3.exceptions.HTTPError(f"Status: {response.status}, Reason: {response.reason}")

			if raw:
				return response

			data = response.data.decode("utf-8")
			break

		except urllib3.exceptions.HTTPError as e:

			if attempt == 2:
				xbmc.log(f"gdrive error: {e}", xbmc.LOGERROR)
				return {}

			xbmc.sleep(1000)

	try:
		data = json.loads(data)
	except json.JSONDecodeError:
		pass

	return data

import json
import time
import datetime

import xbmc

from constants import SETTINGS


def floorDT(dt, interval):
	replace = (dt.minute // interval) * interval
	return dt.replace(minute=replace, second=0, microsecond=0)


def getCurrentTime():
	return floorDT(datetime.datetime.now().time(), 1)


def getElapsedTime(timestamp):
	secondsElapsed = time.time() - float(timestamp)
	hours, remainder = divmod(round(secondsElapsed), 3600)

	if hours:
		return f"{hours} {SETTINGS.getLocalizedString(30140)}" if hours > 1 else f"{hours} {SETTINGS.getLocalizedString(30139)}"

	minutes, seconds = divmod(remainder, 60)

	if minutes:
		return f"{minutes} {SETTINGS.getLocalizedString(30138)}" if minutes > 1 else f"{minutes} {SETTINGS.getLocalizedString(30137)}"
	else:
		return f"{seconds} {SETTINGS.getLocalizedString(30136)}" if seconds > 1 else f"{seconds} {SETTINGS.getLocalizedString(30135)}"


def rfcToTimestamp(dateString):
	# RFC 3339 str to timestamp
	return strptime(dateString, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc).timestamp()


def secondsToHMS(seconds):
	hours, remainder = divmod(round(seconds), 3600)
	minutes, seconds = divmod(remainder, 60)
	time = ""

	if hours:
		time += f"{hours}h"

		if minutes:
			time += f"{minutes}m"

		return time

	if minutes:
		time += f"{minutes}m"

	if seconds:
		time += f"{seconds}s"

	return time


def rpc(query):
	query.update({"jsonrpc": "2.0", "id": 1})
	query = json.dumps(query)
	return json.loads(xbmc.executeJSONRPC(query))


def strptime(dateString, format):

	try:
		return datetime.datetime.strptime(dateString, format)
	except TypeError:
		return datetime.datetime(*time.strptime(dateString, format)[:6])


def strToDatetime(dateString, format="%H:%M"):
	return strptime(dateString, format).time()

import json
import time
import datetime

import xbmc


def floorDT(dt, interval):
	replace = (dt.minute // interval) * interval
	return dt.replace(minute=replace, second=0, microsecond=0)

def getCurrentTime():
	return floorDT(datetime.datetime.now().time(), 1)

def rfcToTimestamp(dateString):
	# RFC 3339 str to timestamp
	return strptime(dateString, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc).timestamp()

def sendJSONRPCCommand(query):
	query = json.dumps(query)
	return json.loads(xbmc.executeJSONRPC(query))

def strptime(dateString, format):

	try:
		return datetime.datetime.strptime(dateString, format)
	except TypeError:
		return datetime.datetime(*time.strptime(dateString, format)[:6])

def strToDatetime(dateString, format="%H:%M"):
	return strptime(dateString, format).time()

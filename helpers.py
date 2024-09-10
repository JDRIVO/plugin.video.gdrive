import json
import datetime

import xbmc


def convertTime(time):
	# RFC 3339 to timestamp
	return datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc).timestamp()

def floorDT(dt, interval):
	replace = (dt.minute // interval) * interval
	return dt.replace(minute = replace, second=0, microsecond=0)

def getCurrentTime():
	floorDT(datetime.datetime.now().time(), 1)

def sendJSONRPCCommand(query):
	query = json.dumps(query)
	return json.loads(xbmc.executeJSONRPC(query))

def strptime(dateString, format):
	return datetime.datetime(*(time.strptime(dateString, format)[:6])).time()

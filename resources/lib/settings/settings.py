import sys
import json
import urllib.parse

import xbmcaddon


class Settings(xbmcaddon.Addon):

	def __init__(self):

		try:
			self.pluginQueries = self.parseQuery(sys.argv[2][1:])
		except Exception:
			self.pluginQueries = None

	@staticmethod
	def parseQuery(query):
		queries = {}

		try:
			queries = urllib.parse.parse_qs(query)
		except Exception:
			return

		q = {key: value[0] for key, value in queries.items()}
		q["mode"] = q.get("mode", "main")
		return q

	def getParameter(self, key, default=""):

		try:
			value = self.pluginQueries[key]

			if value == "true" or value == "True":
				return True
			elif value == "false" or value == "False":
				return False
			else:
				return value

		except Exception:
			return default

	def getParameterInt(self, key, default=0):

		try:
			value = self.pluginQueries[key]

			if value == "true" or value == "True":
				return True
			elif value == "false" or value == "False":
				return False
			else:
				return value

		except Exception:
			return default

	def getSetting(self, key, default=""):

		try:
			value = super().getSetting(key)

			if value == "true" or value == "True":
				return True
			elif value == "false" or value == "False":
				return False
			elif value is None:
				return default
			else:
				return value

		except Exception:
			return default

	def getSettingInt(self, key, default=0):

		try:
			return int(self.getSetting(key))
		except Exception:
			return default

	def getSyncSettings(self):
		SyncSettings = self.getSetting("sync")

		if not SyncSettings:
			return {}
		else:
			return json.loads(SyncSettings)

	def saveSyncSettings(self, SyncSettings):
		self.setSetting("sync", json.dumps(SyncSettings))

import sys
import urllib.parse

import xbmcaddon


class Settings(xbmcaddon.Addon):

	def __init__(self):

		try:
			self.pluginQueries = self.parseQuery(sys.argv[2][1:])
		except Exception:
			self.pluginQueries = None

	def getParameter(self, key, default=None):
		return self._parseValue(self.pluginQueries.get(key), default)

	def getParameterInt(self, key, default=None):

		try:
			return int(self.getParameter(key))
		except ValueError:
			return default

	def getSetting(self, key, default=None):
		return self._parseValue(super().getSetting(key), default)

	def getSettingInt(self, key, default=None):

		try:
			return int(self.getSetting(key))
		except ValueError:
			return default

	@staticmethod
	def parseQuery(queries):

		try:
			query = dict(urllib.parse.parse_qsl(queries))
		except Exception:
			return

		query["mode"] = query.get("mode", "main")
		return query

	@staticmethod
	def _parseValue(value, default):

		if value is None:
			return default

		valueLowerCase = value.lower()

		if valueLowerCase in ("true", "false", "none"):
			return valueLowerCase == "true"
		else:
			return value

import os

import xbmcvfs
import xbmcaddon

from ..database.db_manager import DatabaseManager

ADDON_PATH = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo("profile"))

if not os.path.exists(ADDON_PATH):
	os.mkdir(ADDON_PATH)

CACHE_PATH = os.path.join(ADDON_PATH, "titles_cache.db")


class TitleCacheManager(DatabaseManager):

	def __init__(self):
		newDB = not os.path.exists(CACHE_PATH)
		super().__init__(CACHE_PATH)

		if newDB:
			self._createTables()

	def addMovie(self, data):
		self.insert("movies", data)

	def addSeries(self, data):
		self.insert("series", data)

	def getMovie(self, condition):
		title = self.selectAll("movies", condition)
		if title: return title[0]

	def getSeries(self, condition):
		title = self.selectAll("series", condition)
		if title: return title[0]

	def _createTables(self):
		columns = (
			"original_title TEXT",
			"original_year TEXT",
			"new_title TEXT",
			"new_year TEXT",
			"UNIQUE (original_title, original_year)"
		)

		for table in ("movies", "series"):
			self.createTable(table, columns)

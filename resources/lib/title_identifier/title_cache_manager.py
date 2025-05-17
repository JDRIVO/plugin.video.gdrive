import os

from constants import ADDON_PATH
from ..database.db_manager import DatabaseManager

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
		return self.select("movies", condition, fetchAll=False)

	def getSeries(self, condition):
		return self.select("series", condition, fetchAll=False)

	def _createTables(self):
		columns = (
			"original_title TEXT",
			"original_year TEXT",
			"new_title TEXT",
			"new_year TEXT",
			"UNIQUE (original_title, original_year)"
		)
		[self.createTable(table, columns) for table in ("movies", "series")]

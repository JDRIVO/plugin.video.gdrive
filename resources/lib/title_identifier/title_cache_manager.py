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
		self.movies = []
		self.series = []

		if newDB:
			self._createTables()

	def addMovie(self, data):
		self.movies.append(data)

	def addSeries(self, data):
		self.series.append(data)

	def getMovie(self, condition):
		return self.select("movies", condition=condition, fetchAll=False)

	def getSeries(self, condition):
		return self.select("series", condition=condition, fetchAll=False)

	def insertMovies(self):
		columns = (
			"original_title",
			"original_year",
			"new_title",
			"new_year",
		)
		self.insertMany("movies", columns, self.movies)

	def insertSeries(self):
		columns = (
			"original_title",
			"original_year",
			"new_title",
			"new_year",
		)
		self.insertMany("series", columns, self.series)

	def _createTables(self):
		columns = (
			"original_title TEXT",
			"original_year TEXT",
			"new_title TEXT",
			"new_year TEXT",
			"UNIQUE (original_title, original_year)"
		)
		[self.createTable(table, columns) for table in ("movies", "series")]

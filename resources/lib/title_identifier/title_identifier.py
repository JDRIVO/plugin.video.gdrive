import re
import time
import difflib
import threading

from ..network import http_requester
from ..network.network_helpers import addQueryString
from ..filesystem.fs_helpers import removeProhibitedFSchars

TMDB_URL = "https://api.themoviedb.org/3/search/"
IMDB_URL = "https://www.imdb.com/find/"


class TitleIdentifier:
	lock = threading.Lock()

	def __init__(self, tmdbSettings):
		self.tmdbSettings = tmdbSettings

	def processTitle(self, title, year, media):
		titleLower = title.replace(" ", "").casefold()
		yearStr = str(year)
		isMovie = media == "movie"
		matches = {}
		totalResults, titles = self._getTitlesFromTMDB(title, year, isMovie)

		if titles:
			self._findMatches(matches, titles, titleLower, year, yearStr)

		if year and (not matches or totalResults > 1 and max(matches) < 0.85):
			totalResults, titles = self._getTitlesFromTMDB(title, None, isMovie)
			self._findMatches(matches, titles, titleLower, year, yearStr)

		if matches:
			bestMatch = max(matches)

			if not isMovie or bestMatch >= 0.85:
				return matches[bestMatch]

		if not isMovie:
			return

		titles = self._getTitleFromIMDB(title, year)

		if titles:
			self._findMatches(matches, titles, titleLower, year, yearStr)

			if matches:
				return matches[max(matches)]

	def _findMatches(self, matches, candidates, title, year, yearStr):

		for candidate in candidates:
			candidateTitle, candidateYear = candidate
			candidateTitle = removeProhibitedFSchars(candidateTitle)
			candidateTitleLower = candidateTitle.replace(" ", "").casefold()
			candidateYearInt = int(candidateYear)
			titleSimilarity = difflib.SequenceMatcher(None, title, candidateTitleLower).ratio()

			if titleSimilarity in matches:
				matchesYear = matches[titleSimilarity][1]

				if not year or matchesYear == yearStr or abs(int(matchesYear) - year) < 2:
					continue

			if (year and abs(candidateYearInt - year) < 2) or not year:

				if titleSimilarity >= 0.5:
					matches[titleSimilarity] = candidateTitle, candidateYear
				elif candidateTitleLower in title or title in candidateTitleLower:
					matches[titleSimilarity] = candidateTitle, candidateYear

	def _getTitleFromIMDB(self, title, year):
		url = addQueryString(IMDB_URL, {"q": f"{title} {year}", "s": "tt", "ttype": "ft", "ref_": "fn_ft"})

		with self.lock:
			delay = 2
			attempts = 3

			for _ in range(attempts):
				response = http_requester.request(url)

				if response:
					match = re.search('"titleNameText":"(.*?)".*?"titleReleaseText":"(.*?)"', response)

					if match:
						return [(re.sub(r"\\u([0-9a-fA-F]{4})", lambda x: chr(int(x.group(1), 16)), match.group(1)), match.group(2))]

					break

				time.sleep(delay)

	def _getTitlesFromTMDB(self, title, year, isMovie):
		url = TMDB_URL + "movie" if isMovie else TMDB_URL + "tv"

		if year:
			url = addQueryString(url, {"query": title, "year" if isMovie else "first_air_date_year": year, **self.tmdbSettings})
		else:
			url = addQueryString(url, {"query": title, **self.tmdbSettings})

		delay = 2
		attempts = 3

		for _ in range(attempts):
			response = http_requester.request(url)

			if response:
				break

			time.sleep(delay)

		if not response:
			return 0, []

		totalResults = response["total_results"]
		titles = []

		for result in response["results"][:3]:

			if isMovie:
				title = result["title"]
				year = result["release_date"][:4]
				originalTitle = result["original_title"]
			else:
				title = result["name"]
				year = result["first_air_date"][:4]
				originalTitle = result["original_name"]

			if not title or not year:
				continue

			if (title, year) not in titles:
				titles.append((title, year))

			if (originalTitle, year) not in titles:
				titles.append((originalTitle, year))

		return totalResults, titles

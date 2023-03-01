from . import file
from . import helpers


class Video(file.File):
	title = None
	year = None
	ptn_name = None
	duration = None
	metadata = {}
	aspect_ratio = None
	video_width = None
	video_height = None
	video_codec = None
	audio_codec = None
	audio_channels = None
	contents = None
	hdr = None

	def setContents(self, data):
		title = data.get("title")
		year = data.get("year")
		season = data.get("season")
		episode = data.get("episode")
		self.ptn_name = str((title, year, season, episode))

		if title is not None:
			self.title = title

		if year is not None:
			self.year = year

		if season is not None:
			self.season = str(season)

		if episode is not None:
			self.episode = episode

		del data["year"]
		del data["title"]
		del data["season"]
		del data["episode"]
		self.contents = data

class Movie(Video):

	def __str__(self):
		return "Movie"

	def formatName(self):
		# Produces a conventional name that can be understood by library scrapers
		data = helpers.getTMDBtitle("movie", self.title, self.year)

		if data:
			title, year = data
			return {
				"title": title,
				"year": year,
				"filename": f"{title} ({year})",
			}

class Episode(Video):
	season = None
	episode = None

	def __str__(self):
		return "Episode"

	def formatName(self):
		# Produces a conventional name that can be understood by library scrapers

		if int(self.season) < 10:
			season = f"0{self.season}"
		else:
			season = self.season

		if isinstance(self.episode, int):

			if self.episode < 10:
				episode = f"0{self.episode}"
			else:
				episode = str(self.episode)

		else:
			modifiedEpisode = ""

			for e in self.episode:

				if e < 10:
					append = f"0{e}"
				else:
					append = e

				if e != self.episode[-1]:
					modifiedEpisode += f"{append}-"
				else:
					modifiedEpisode += str(append)

			episode = modifiedEpisode

		data = helpers.getTMDBtitle("episode", self.title, self.year)

		if data:
			title, year = data
			return {
				"title": title,
				"year": year,
				"filename": f"{title} S{season}E{episode}",
			}

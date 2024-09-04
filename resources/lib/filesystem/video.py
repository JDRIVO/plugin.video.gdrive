from . import helpers
from .file import File


class Video(File):
	media = None
	title = None
	year = None
	ptnName = None
	duration = None
	videoWidth = None
	videoHeight = None
	aspectRatio = None
	videoCodec = None
	audioCodec = None
	audioChannels = None
	hdr = None
	contents = None

	def setData(self, video, metadata):
		self.title = video.get("title")
		self.year = video.get("year")
		self.contents = metadata


class Movie(Video):

	def setData(self, video, metadata):
		super().setData(video, metadata)
		self.ptnName = str((self.title, self.year))

	def formatName(self, tmdbSettings, imdbLock):
		data = helpers.getTMDBtitle("movie", self.title, self.year, tmdbSettings, imdbLock)

		if data:
			title, year = data
			return {"title": title, "year": year, "filename": f"{title} ({year})"}


class Episode(Video):
	season = None
	episode = None

	def setData(self, video, metadata):
		super().setData(video, metadata)
		self.season = video.get("season")
		self.episode = video.get("episode")
		self.ptnName = str((self.title, self.year, self.season, self.episode))

	def formatName(self, tmdbSettings, imdbLock):
		season = f"{int(self.season):02d}"

		if isinstance(self.episode, int):
			episode = f"{self.episode:02d}"
		else:
			episode = "-".join(f"{e:02d}" for e in self.episode)

		data = helpers.getTMDBtitle("episode", self.title, self.year, tmdbSettings, imdbLock)

		if data:
			title, year = data
			return {"title": title, "year": year, "filename": f"{title} S{season}E{episode}"}

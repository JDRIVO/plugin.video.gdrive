from .file import File


class Video(File):

	def __init__(self):
		super().__init__()
		self.media = None
		self.title = None
		self.year = None
		self.language = None
		self.metadata = None

	def getSTRMContents(self, driveID):
		self.metadata.update({"drive_id": driveID, "file_id": self.id, "encrypted": str(self.encrypted)})
		return "plugin://plugin.video.gdrive/?mode=video" + "".join([f"&{k}={v}"for k, v in self.metadata.items() if v])

	def setData(self, video, metadata):
		self.title = video["title"]
		self.year = video["year"]
		self.language = video["language"]
		self.metadata = metadata


class Movie(Video):

	def formatName(self, cacheManager, titleIdentifier):
		titleInfo = cacheManager.getMovie({"original_title": self.title, "original_year": self.year})

		if titleInfo:
			title = titleInfo["new_title"]
			year = titleInfo["new_year"]
			return {"title": title, "year": year, "filename": f"{title} ({year})"}

		titleInfo = titleIdentifier.processTitle(self.title, self.year, "movie")

		if titleInfo:
			title, year = titleInfo
			cacheManager.addMovie({"original_title": self.title, "original_year": self.year, "new_title": title, "new_year": year})
			return {"title": title, "year": year, "filename": f"{title} ({year})"}


class Episode(Video):

	def __init(self):
		self.season = None
		self.episode = None

	def setData(self, video, metadata):
		super().setData(video, metadata)
		self.season = video["season"]
		self.episode = video["episode"]

	def formatName(self, cacheManager, titleIdentifier):
		season = f"{int(self.season):02d}"

		if isinstance(self.episode, int):
			episode = f"{self.episode:02d}"
		else:
			episode = "-".join(f"{e:02d}" for e in self.episode)

		titleInfo = cacheManager.getSeries({"original_title": self.title, "original_year": self.year})

		if titleInfo:
			title = titleInfo["new_title"]
			return {"title": title, "year": titleInfo["new_year"], "filename": f"{title} S{season}E{episode}"}

		titleInfo = titleIdentifier.processTitle(self.title, self.year, "episode")

		if titleInfo:
			title, year = titleInfo
			cacheManager.addSeries({"original_title": self.title, "original_year": self.year, "new_title": title, "new_year": year})
			return {"title": title, "year": year, "filename": f"{title} S{season}E{episode}"}

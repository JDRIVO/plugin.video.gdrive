from .video import Video


class Subtitles(Video):
	language = None

	def setData(self, video, metadata):
		super().setData(video, metadata)
		self.language = video.get("language")

		if self.media == "movie":
			self.ptnName = str((self.title, self.year))
		else:
			self.ptnName = str((self.title, self.year, video.get("season"), video.get("episode")))

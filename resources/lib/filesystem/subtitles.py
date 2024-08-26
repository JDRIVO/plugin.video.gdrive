from .video import Video


class Subtitles(Video):
	language = None

	def setData(self, video, metadata):
		super().setData(video, metadata)
		self.language = video.get("language")

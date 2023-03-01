from . import video


class Subtitles(video.Video):
	language = None

	def setContents(self, data):
		super().setContents(data)
		self.language = data.get("language")

from threading import Thread

import xbmc


class Player(xbmc.Player):

	def __init__(self, dbID, dbType, widget, trackProgress, settings):
		self.videoDuration = self.started = self.close = False
		self.dbID = dbID
		self.dbType = dbType

		self.widget = widget
		self.trackProgress = trackProgress
		self.monitor = xbmc.Monitor()

		if self.dbType == "movie":
			self.markedWatchedPoint = float(settings.getSetting("movie_watch_time"))
		elif self.dbType == "episode":
			self.markedWatchedPoint = float(settings.getSetting("tv_watch_time"))

		xbmc.sleep(2000)

		while not self.monitor.abortRequested() and not self.videoDuration:

			try:
				self.videoDuration = self.getTotalTime()
			except Exception:
				self.close = True
				return

			if self.monitor.waitForAbort(0.1):
				break

		Thread(target=self.updateTime).start()
		self.started = True

	def onPlayBackStarted(self):

		if not self.started:
			return

		if self.trackProgress:
			self.markVideoWatched()

		self.close = True

	def onPlayBackEnded(self):
		self.close = True

	def onPlayBackStopped(self):

		if self.trackProgress:
			self.markVideoWatched()

		self.close = True

	def onPlayBackSeek(self, time, seekOffset):
		self.time = time

	def updateTime(self):

		while not self.monitor.abortRequested() and self.isPlaying():

			try:
				self.time = self.getTime()
			except Exception:
				pass

			if self.monitor.waitForAbort(1):
				break

	def markVideoWatched(self):

		if self.dbType not in ("movie", "episode"):
			return

		try:
			videoProgress = self.time / self.videoDuration * 100
		except Exception:
			return

		if videoProgress >= self.markedWatchedPoint:

			if self.dbType == "movie":
				xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.SetMovieDetails", "params": {"movieid": %s, "playcount": 1, "resume": {"position": 0, "total": 0}}}' % self.dbID)
			elif self.dbType == "episode":
				xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.SetEpisodeDetails", "params": {"episodeid": %s, "playcount": 1, "resume": {"position": 0, "total": 0}}}' % self.dbID)

	def refreshVideo(self):

		if self.isMovie:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.RefreshMovie", "params": {"movieid": %s}}' % self.dbID)
		else:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.RefreshEpisode", "params": {"episodeid": %s}}' % self.dbID)

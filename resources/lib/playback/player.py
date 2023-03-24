from threading import Thread

import xbmc

import constants


class Player(xbmc.Player):

	def __init__(self, dbID, dbType, trackProgress):
		self.dbID = dbID
		self.dbType = dbType
		self.trackProgress = trackProgress
		self.close = False
		self.videoDuration = None
		self.monitor = xbmc.Monitor()

		if self.dbType == "movie":
			self.markedWatchedPoint = float(constants.settings.getSetting("movie_watch_time"))
		elif self.dbType == "episode":
			self.markedWatchedPoint = float(constants.settings.getSetting("tv_watch_time"))

		while not self.monitor.abortRequested() and not self.videoDuration and not self.close:

			try:
				self.videoDuration = self.getTotalTime()
			except Exception:
				pass

			if self.monitor.waitForAbort(0.1):
				return

		Thread(target=self.updateTime).start()

	def onPlayBackEnded(self):
		self.close = True

	def onPlayBackStopped(self):

		if self.trackProgress and self.dbType in ("movie", "episode"):

			for _ in range(3):
				self.markVideoWatched()
				xbmc.sleep(1000)

		self.close = True

	def onPlayBackSeek(self, time, seekOffset):
		self.time = time

	def updateTime(self):

		while not self.monitor.abortRequested() and not self.close:

			try:
				self.time = self.getTime()
			except Exception:
				pass

			if self.monitor.waitForAbort(1):
				break

	def markVideoWatched(self):

		try:
			videoProgress = self.time / self.videoDuration * 100
		except Exception:
			return

		if videoProgress >= self.markedWatchedPoint:

			if self.dbType == "movie":
				xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.SetMovieDetails", "params": {"movieid": %s, "playcount": 1, "resume": {"position": 0, "total": 0}}}' % self.dbID)
			elif self.dbType == "episode":
				xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.SetEpisodeDetails", "params": {"episodeid": %s, "playcount": 1, "resume": {"position": 0, "total": 0}}}' % self.dbID)

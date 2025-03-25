from threading import Thread

import xbmc

from constants import SETTINGS
from helpers import sendJSONRPCCommand


class VideoPlayer(xbmc.Player):

	def __init__(self, dbID, dbType):
		self.dbID = int(dbID) if dbID else dbID
		self.dbType = dbType
		self.close = False
		self.time = None
		self.videoDuration = None
		self.monitor = xbmc.Monitor()

		if self.dbType == "movie":
			self.markedWatchedPoint = float(SETTINGS.getSetting("movie_watch_time"))
		elif self.dbType == "episode":
			self.markedWatchedPoint = float(SETTINGS.getSetting("episode_watch_time"))

		while not self.monitor.abortRequested() and not self.videoDuration and not self.close:

			try:
				self.videoDuration = self.getTotalTime()
			except Exception:
				pass

			if self.monitor.waitForAbort(0.1):
				return

		Thread(target=self._updateTime).start()

	def onPlayBackEnded(self):
		self.close = True

	def onPlayBackSeek(self, time, seekOffset):
		self.time = time

	def onPlayBackStopped(self):

		if self.dbID and self.dbType in ("movie", "episode"):

			for _ in range(3):
				self._markVideoWatched()
				xbmc.sleep(1000)

		self.close = True

	def _markVideoWatched(self):

		try:
			videoProgress = self.time / self.videoDuration * 100
		except TypeError:
			return

		if videoProgress >= self.markedWatchedPoint:

			if self.dbType == "movie":
				query = {
					"jsonrpc": "2.0",
					"id": 1,
					"method": "VideoLibrary.SetMovieDetails",
					"params": {"movieid": self.dbID, "playcount": 1, "resume": {"position": 0, "total": 0}},
				}
			else:
				query = {
					"jsonrpc": "2.0",
					"id": 1,
					"method": "VideoLibrary.SetEpisodeDetails",
					"params": {"episodeid": self.dbID, "playcount": 1, "resume": {"position": 0, "total": 0}},
				}

			sendJSONRPCCommand(query)

	def _updateTime(self):

		while not self.monitor.abortRequested() and not self.close:

			try:
				self.time = self.getTime()
			except Exception:
				pass

			if self.monitor.waitForAbort(1):
				break

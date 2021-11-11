import time
import xbmc
import constants
from threading import Thread
from resources.lib import settings

settingsModule = settings.Settings(constants.addon)


class gPlayer(xbmc.Player):

	def __init__(self, *args, **kwargs):
		xbmc.Player.__init__(self)
		self.dbID = kwargs["dbID"]
		self.dbType = kwargs["dbType"]
		self.widget = kwargs["widget"]
		self.isExit = False
		self.videoDuration = None

		if self.dbType == "movie":
			self.isMovie = True
			self.markedWatchedPoint = float(settingsModule.movieWatchTime)
		else:
			self.isMovie = False
			self.markedWatchedPoint = float(settingsModule.tvWatchTime)

		time.sleep(2)

		while not self.videoDuration:

			try:
				self.videoDuration = self.getTotalTime()
			except:
				self.isExit = True
				break

			time.sleep(0.1)

		t = Thread(target=self.saveProgress)
		t.start()

	def onPlayBackEnded(self):
		self.isExit = True

	def onPlayBackStopped(self):
		self.updateProgress(False)
		self.isExit = True

	def onPlayBackSeek(self, time, seekOffset):
		self.time = time

	def saveProgress(self):

		while self.isPlaying():
			self.updateProgress()
			time.sleep(1)

	def updateProgress(self, thread=True):

		try:
			self.time = self.getTime()
		except:
			pass

		try:
			videoProgress = self.time / self.videoDuration * 100
		except:
			return

		if videoProgress < self.markedWatchedPoint:
			watched = False
			func = self.updateResumePoint
		else:
			watched = True
			func = self.markVideoWatched

		if thread:
			func()
		else:

			if (watched or self.time < 180) and self.widget and self.isMovie:
				func()
				self.refreshVideo()
				return

			timeEnd = time.time() + 3

			while time.time() < timeEnd:
				func()
				time.sleep(1)

	def updateResumePoint(self):

		if self.isMovie:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.SetMovieDetails", "params": {"movieid": %s, "playcount": 0, "resume": {"position": %d, "total": %d}}}' % (self.dbID, self.time, self.videoDuration))
		else:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.SetEpisodeDetails", "params": {"episodeid": %s, "playcount": 0, "resume": {"position": %d, "total": %d}}}' % (self.dbID, self.time, self.videoDuration))

	def markVideoWatched(self):

		if self.isMovie:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.SetMovieDetails", "params": {"movieid": %s, "playcount": 1, "resume": {"position": 0, "total": 0}}}' % self.dbID)
		else:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.SetEpisodeDetails", "params": {"episodeid": %s, "playcount": 1, "resume": {"position": 0, "total": 0}}}' % self.dbID)

	def refreshVideo(self):

		if self.isMovie:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.RefreshMovie", "params": {"movieid": %s}}' % self.dbID)
		else:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.RefreshEpisode", "params": {"episodeid": %s}}' % self.dbID)

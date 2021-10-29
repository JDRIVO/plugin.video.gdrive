import time
import xbmc
import constants
from threading import Thread
from resources.lib import settings

addon = constants.addon
settingsModule = settings.settings(addon)

class gPlayer(xbmc.Player):

	def __init__(self, *args, **kwargs):
		xbmc.Player.__init__(self)
		self.dbID = kwargs["dbID"]
		self.dbType = kwargs["dbType"]
		self.monitor = xbmc.Monitor()
		self.isExit = False
		self.videoDuration = None

		if self.dbType == "movie":
			self.isMovie = True
			self.markedWatchedPoint = float(settingsModule.movieWatchTime)
		else:
			self.isMovie = False
			self.markedWatchedPoint = float(settingsModule.tvWatchTime)

	def onPlayBackStarted(self):

		while not self.videoDuration:

			try:
				self.videoDuration = self.getTotalTime()
			except:
				self.isExit = True
				break

			xbmc.sleep(100)

		t = Thread(target=self.saveTime)
		t.setDaemon(True)
		t.start()
		t = Thread(target=self.saveProgress)
		t.setDaemon(True)
		t.start()

	def saveTime(self):

		while self.isPlaying():
			self.time = self.getTime()
			xbmc.sleep(100)

	def saveProgress(self):

		while self.isPlaying():
			self.updateVideoStats()
			xbmc.sleep(1000)

	def updateVideoStats(self):

		try:
			videoProgress = self.time / self.videoDuration * 100
		except:
			return

		if videoProgress < self.markedWatchedPoint:
			self.updateResumePoint()
		else:
			self.markVideoWatched()

	def onPlayBackStopped(self):
		self.updateVideoStats()
		xbmc.executebuiltin("ReloadSkin")
		self.isExit = True

	def onPlayBackEnded(self):
		self.updateVideoStats()
		xbmc.executebuiltin("ReloadSkin")
		self.isExit = True

	def updateResumePoint(self):

		if self.isMovie:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.SetMovieDetails", "params": {"movieid": %s, "resume": {"position": %d, "total": %d} } }' % (self.dbID, self.time, self.videoDuration ) )
		else:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.SetEpisodeDetails", "params": {"episodeid": %s, "resume": {"position": %d, "total": %d} } }' % (self.dbID, self.time, self.videoDuration) )

	def markVideoWatched(self):

		if self.isMovie:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.SetMovieDetails", "params": {"movieid": %s, "playcount": 1 , "resume": {"position": 0} } }' % self.dbID)
		else:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.SetEpisodeDetails", "params": {"episodeid": %s, "playcount": 1 , "resume": {"position": 0} } }' % self.dbID)

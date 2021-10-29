import xbmc
import constants
from threading import Thread
from resources.lib import settings

settingsModule = settings.settings(constants.addon)


class gPlayer(xbmc.Player):

	def __init__(self, *args, **kwargs):
		xbmc.Player.__init__(self)
		self.dbID = kwargs["dbID"]
		self.dbType = kwargs["dbType"]
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

		t = Thread(target=self.saveProgress)
		t.setDaemon(True)
		t.start()

	def saveProgress(self):

		while self.isPlaying():
			self.updateProgress()
			xbmc.sleep(1000)

	def updateProgress(self):

		try:
			self.time = self.getTime()
			videoProgress = self.time / self.videoDuration * 100
		except:
			return

		if videoProgress < self.markedWatchedPoint:
			self.updateResumePoint()
		else:
			self.markVideoWatched()

	def onPlayBackStopped(self):
		self.updateProgress()
		self.isExit = True

	def onPlayBackEnded(self):
		self.updateProgress()
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

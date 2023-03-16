import os
import time
import queue
import threading

import xbmc


class ThreadPool(queue.Queue, xbmc.Monitor):

	def __init__(self, maxWorkers=None):
		super().__init__()

		if not maxWorkers:
			maxWorkers = min(32, (os.cpu_count() or 1) + 4)

		self.maxWorkers = maxWorkers
		self.threadShutdown = False
		self.tasksRemaining = {"tasks": 0}
		self.createWorkers()
		threading.Thread(target=self.abortChecker).start()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.shutdown()

	def abortChecker(self):

		while not self.abortRequested() and not self.threadShutdown:

			if self.waitForAbort(0.1):
				self.threadShutdown = True

	def createWorkers(self):

		for _ in range(self.maxWorkers):
			threading.Thread(target=self.worker, daemon=True).start()

	def decrementTasks(self):
		self.tasksRemaining["tasks"] -= 1

	def incrementTasks(self):
		self.tasksRemaining["tasks"] += 1

	def setTasks(self, taskNumber):
		self.tasksRemaining["tasks"] = taskNumber

	def worker(self):

		while not self.threadShutdown:

			try:
				data = self.get_nowait()

				if data is None:
					self.put(None)
					return

				func, args = data
				func(*args)
			except queue.Empty:
				time.sleep(0.1)
				continue

			except Exception as e:
				xbmc.log("gdrive error: " + str(e), xbmc.LOGERROR)

			self.decrementTasks()

	def map(self, func, args):
		self.setTasks(len(args))
		[self.put((func, args_)) for args_ in args]

	def submit(self, func, *args):
		self.incrementTasks()
		self.put((func, args))

	def shutdown(self):

		while self.tasksRemaining["tasks"] and not self.threadShutdown:
			time.sleep(0.1)

		self.put(None)

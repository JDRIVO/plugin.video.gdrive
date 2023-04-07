import os
import queue
import threading
import traceback

import xbmc


class ThreadPool(queue.Queue, xbmc.Monitor):

	def __init__(self, maxWorkers=None):
		super().__init__()

		if not maxWorkers:
			maxWorkers = min(32, (os.cpu_count() or 1) + 4)

		self.maxWorkers = maxWorkers
		self.tasksRemaining = {"tasks": 0}
		self.createWorkers()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.shutdown()

	def decrementTasks(self):
		self.tasksRemaining["tasks"] -= 1

	def incrementTasks(self):
		self.tasksRemaining["tasks"] += 1

	def setTasks(self, taskNumber):
		self.tasksRemaining["tasks"] = taskNumber

	def createWorkers(self):

		for _ in range(self.maxWorkers):
			threading.Thread(target=self.worker).start()

	def worker(self):

		while not self.abortRequested():

			try:
				data = self.get_nowait()

				if data is None:
					self.put(None)
					return

				func, args = data
				func(*args)
			except queue.Empty:

				if self.waitForAbort(0.1):
					return

				continue

			except Exception as e:
				xbmc.log(f"gdrive error: {e}: {''.join(traceback.format_tb(e.__traceback__))}", xbmc.LOGERROR)

			self.decrementTasks()

	def map(self, func, args):
		self.setTasks(len(args))
		[self.put((func, args_)) for args_ in args]

	def submit(self, func, *args):
		self.incrementTasks()
		self.put((func, args))

	def shutdown(self):

		while self.tasksRemaining["tasks"] and not self.abortRequested():

			if self.waitForAbort(0.1):
				break

		self.put(None)

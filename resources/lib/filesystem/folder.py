from . import helpers


class Folder:

	def __init__(self, id, parentID, name, path, modifiedTime=None):
		self.id = id
		self.parentID = parentID
		self.name = name
		self.path = path
		self.modifiedTime = helpers.convertTime(modifiedTime) if modifiedTime else None
		self.files = {
			"strm": [],
			"video": [],
			"media_assets": {},
		}

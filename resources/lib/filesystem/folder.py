class Folder:

	def __init__(self, id, parentID, name, path):
		self.id = id
		self.parentID = parentID
		self.name = name
		self.path = path
		self.files = {
			"strm": [],
			"video": [],
			"media_assets": {},
		}

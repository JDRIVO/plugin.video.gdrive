import os
import secrets

from constants import ADDON_PATH
from .obscurer import obscure, unobscure
from ..filesystem.file_operations import FileOperations

if not os.path.exists(ADDON_PATH):
	os.mkdir(ADDON_PATH)

PROFILES_FILE = os.path.join(ADDON_PATH, "encryption_profiles.pkl")


class ProfileManager:

	def __init__(self):
		self.fileOperations = FileOperations()
		self.setProfiles()

	def addProfile(self, profile):
		profile = self._obscureData(profile)

		while profile.id in self.profiles:
			profile.id = secrets.token_hex(6)

		self.profiles[profile.id] = profile
		self._saveProfiles()

	def deleteProfile(self, id):
		del self.profiles[id]
		self._saveProfiles()

	def exportProfiles(self, filePath):
		self._saveProfiles(filePath)

	def getProfile(self, id):

		if profile := self.profiles.get(id):
			return self._unobscureData(profile)

	def getProfileEntries(self):
		entries = sorted([(id, profile.name) for id, profile in self.profiles.items()], key=lambda x: x[1].lower())
		ids, names = zip(*entries) if entries else ((), ())
		return ids, names

	def importProfiles(self, filePath):
		profiles = self._loadProfiles(filePath)

		if not profiles:
			return

		for profile in profiles.values():

			while profile.id in self.profiles:
				profile.id = secrets.token_hex(6)

			self.profiles[profile.id] = profile

		self._saveProfiles()
		return True

	def setProfiles(self):
		self.profiles = self._loadProfiles() or {}

	def updateProfile(self, id, profile):
		profile = self._obscureData(profile)
		self.profiles[id] = profile
		self._saveProfiles()

	def _loadProfiles(self, filePath=PROFILES_FILE):
		return self.fileOperations.loadPickleFile(filePath)

	@staticmethod
	def _obscureData(profile):
		profile.password = obscure(profile.password)

		if profile.salt:
			profile.salt = obscure(profile.salt)

		return profile

	def _saveProfiles(self, filePath=PROFILES_FILE):
		self.fileOperations.savePickleFile(self.profiles, filePath)

	@staticmethod
	def _unobscureData(profile):
		profile.password = unobscure(profile.password)

		if profile.salt:
			profile.salt = unobscure(profile.salt)

		return profile

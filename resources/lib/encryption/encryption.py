from abc import ABC, abstractmethod

from .rclone.crypt import Crypt
from .gdrive.encryptor import Encryptor
from .profile_manager import ProfileManager
from .encryption_types import EncryptionType

profileManager = ProfileManager()


class EncryptionStrategy(ABC):

	@abstractmethod
	def decryptDirName(self, name):
		pass

	@abstractmethod
	def decryptFilename(self, name, fileExtension, mimeType):
		pass

	@abstractmethod
	def decryptStream(self, *args, **kwargs):
		pass

	@abstractmethod
	def downloadFile(self, response, filePath):
		pass


class GDriveAdaptor(EncryptionStrategy):

	def __init__(self, profile):
		self.encryptor = Encryptor(salt=profile.salt, saltPassword=profile.password)
		self.filenameEncryption = True
		self.encryptData = True
		self.encryptDirNames = profile.encryptDirNames

	def decryptDirName(self, name):

		if not self.encryptDirNames:
			return name

		try:
			return self.encryptor.decryptString(name)
		except Exception:
			return name

	def decryptFilename(self, name, fileExtension, mimeType):

		if mimeType != "application/octet-stream":
			return name

		if fileExtension:
			return None

		try:
			return self.encryptor.decryptString(name)
		except Exception:
			return None

	def decryptStream(self, response, wfile, chunkOffset):
		self.encryptor.decryptStreamChunk(response, wfile, chunkOffset)

	def downloadFile(self, response, filePath):
		self.encryptor.decryptStream(response, filePath)


class RcloneAdaptor(EncryptionStrategy):

	def __init__(self, profile):
		password = profile.password
		salt = profile.salt
		filenameEncoding = profile.filenameEncoding
		filenameEncryption = profile.filenameEncryption
		suffix = profile.suffix
		self.encryptData = profile.encryptData
		self.filenameEncryption = filenameEncryption != "off"
		self.encryptDirNames = profile.encryptDirNames
		self.suffix = suffix if suffix.startswith(".") else f".{suffix}"
		self.encryptor = Crypt(password, salt, nameEncoding=filenameEncoding) if salt else Crypt(password, nameEncoding=filenameEncoding)

		if self.filenameEncryption:
			self.decryptName = self.encryptor.name.standard_decrypt if filenameEncryption == "standard" else self.encryptor.name.obfuscate_decrypt

	def decryptDirName(self, name):

		if not self.encryptDirNames:
			return name

		try:
			return self.decryptName(name)
		except Exception:
			return name

	def decryptFilename(self, name, fileExtension, mimeType):

		if fileExtension:
			return name if self.filenameEncryption else name[:-len(self.suffix)] if name.endswith(self.suffix) else name
		else:

			try:
				return self.decryptName(name)
			except Exception:
				return None

	def decryptStream(self, response, wfile, blockIndex, blockOffset):
		self.encryptor.file.decryptStreamChunk(response, wfile, blockIndex, blockOffset)

	def downloadFile(self, response, filePath):
		self.encryptor.file.decryptStream(response, filePath)


class EncryptionHandler:

	def __getattr__(self, name):
		return getattr(self._strategy, name, False)

	def decryptDirName(self, name):
		return self._strategy.decryptDirName(name)

	def decryptFilename(self, name, fileExtension, mimeType):
		return self._strategy.decryptFilename(name, fileExtension, mimeType)

	def decryptStream(self, *args, **kwargs):
		return self._strategy.decryptStream(*args, **kwargs)

	def downloadFile(self, response, filePath):
		self._strategy.downloadFile(response, filePath)
		response.release_conn()

	def setEncryptor(self, id):
		profileManager.setProfiles()
		self.profile = profileManager.getProfile(id)

		if not self.profile:
			return

		if self.profile.type == EncryptionType.GDRIVE:
			self.type = EncryptionType.GDRIVE
			self._strategy = GDriveAdaptor(self.profile)
		else:
			self.type = EncryptionType.RCLONE
			self._strategy = RcloneAdaptor(self.profile)

		return True

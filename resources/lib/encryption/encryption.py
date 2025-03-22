import re
from enum import Enum
from abc import ABC, abstractmethod

from .rclone.crypt import Crypt
from .gdrive.encryptor import Encryptor


class Encryptors(Enum):
	GDRIVE = "gDrive"
	RCLONE = "RCLONE"


class EncryptionStrategy(ABC):

	@abstractmethod
	def decryptFilename(self, name, fileExtension, mimeType):
		pass

	@abstractmethod
	def decryptDirName(self, name):
		pass

	@abstractmethod
	def decryptStream(self, *args, **kwargs):
		pass

	@abstractmethod
	def downloadFile(self, response, filePath):
		pass

	@abstractmethod
	def isEnabled(self, settings):
		pass


class GdriveAdaptor(EncryptionStrategy):

	def __init__(self, settings):
		self.settings = settings
		self.encryptor = Encryptor(settings=self.settings)
		self.filenameEncryption = True
		self.encryptData = True

	def decryptDirName(self, name):
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

	def isEnabled(self, settings):

		if self.settings.getSetting("crypto_password") and self.settings.getSetting("crypto_salt"):
			return True


class RcloneAdaptor(EncryptionStrategy):

	def __init__(self, settings):
		self.settings = settings
		password = self.settings.getSetting("crypto_password")
		saltPassword = self.settings.getSetting("salt_password")
		filenameEncoding = self.settings.getSetting("filename_encoding")
		filenameEncryption = self.settings.getSetting("filename_encyption")
		self.encryptData = self.settings.getSetting("encrypt_data")
		self.filenameEncryption = filenameEncryption != "off"
		self.encryptDirNames = self.settings.getSetting("encrypt_dir_names")
		self.suffix = settings.getSetting("suffix")
		self.encryptor = Crypt(password, saltPassword, nameEncoding=filenameEncoding)

		if self.filenameEncryption:
			self.decryptName = self.encryptor.Name.standard_decrypt if filenameEncryption == "standard" else self.encryptor.Name.obfuscate_decrypt

	def decryptDirName(self, name):

		if not self.encryptDirNames:
			return name

		try:
			return self.decryptName(name)
		except Exception:
			return name

	def decryptFilename(self, name, fileExtension, mimeType):

		if fileExtension:

			if not self.filenameEncryption:
				return re.sub(f"{self.suffix}$", "", name)
			else:
				return name

		else:

			try:
				return self.decryptName(name)
			except Exception:
				return None

	def decryptStream(self, response, wfile, blockIndex, blockOffset):
		self.encryptor.File.decryptStreamChunk(response, wfile, blockIndex, blockOffset)

	def downloadFile(self, response, filePath):
		return self.encryptor.File.decryptStream(response, filePath)

	def isEnabled(self, settings):

		if self.settings.getSetting("crypto_password"):
			return True


class EncryptionHandler:

	def __init__(self, settings):
		self.settings = settings
		self.setEncryptor()

	def __getattr__(self, name):
		return getattr(self._strategy, name, False)

	def decryptFilename(self, name, fileExtension, mimeType):
		return self._strategy.decryptFilename(name, fileExtension, mimeType)

	def decryptDirName(self, name):
		return self._strategy.decryptDirName(name)

	def decryptStream(self, *args, **kwargs):
		return self._strategy.decryptStream(*args, **kwargs)

	def downloadFile(self, response, filePath):
		self._strategy.downloadFile(response, filePath)
		response.release_conn()

	def isEnabled(self):
		return self._strategy.isEnabled(self.settings)

	def setEncryptor(self):

		if self.settings.getSetting("encryption_type") == Encryptors.GDRIVE.value:
			self.type = Encryptors.GDRIVE
			self._strategy = GdriveAdaptor(self.settings)
		else:
			self.type = Encryptors.RCLONE
			self._strategy = RcloneAdaptor(self.settings)

# http://stackoverflow.com/questions/6425131/encrpyt-decrypt-data-in-python-with-salt

import os
import base64
import random
import string
import struct
import hashlib

try:
	import Cryptodome.Random
	from Cryptodome.Cipher import AES
	from Cryptodome.Hash import SHA256
	from Cryptodome.PublicKey import RSA
	from Cryptodome.Signature import pkcs1_15
except Exception:
	import Crypto.Random
	from Crypto.Cipher import AES
	from Crypto.Hash import SHA256
	from Crypto.PublicKey import RSA
	from Crypto.Signature import pkcs1_15


class Encryptor:
	# Salt size in bytes
	SALT_SIZE = 32
	# Number of iterations in the key generation
	NUMBER_OF_ITERATIONS = 20
	# The size multiple required for AES
	AES_MULTIPLE = 16

	def __init__(self, saltFile=None, saltPassword=None, settings=None):
		self._setup(saltFile, saltPassword, settings)

	def decryptFile(self, inFilename, outFilename=None, chunkSize=24 * 1024):
		""" Decrypts a file using AES (CBC mode) with the
			given key. Parameters are similar to encryptFile,
			with one difference: outFilename, if not supplied
			will be inFilename without its last extension
			(i.e. if inFilename is 'aaa.zip.enc' then
			outFilename will be 'aaa.zip')
		"""

		if not outFilename:
			outFilename = os.path.splitext(inFilename)[0]

		with open(inFilename, "rb") as inFile:
			origSize = struct.unpack("<Q", inFile.read(struct.calcsize("Q")))[0]
			# iv = inFile.read(16)
			# decryptor = AES.new(key, AES.MODE_CBC, iv)
			# key = _generateKey(password, salt, NUMBER_OF_ITERATIONS)
			decryptor = AES.new(self.key, AES.MODE_ECB)

			with open(outFilename, "wb") as outFile:

				while True:
					chunk = inFile.read(chunkSize)

					if len(chunk) == 0:
						break

					outFile.write(decryptor.decrypt(chunk))

				outFile.truncate(origSize)

	def decryptFilename(self, filename):
		decryptedFilename = self.decryptString(filename)

		if decryptedFilename:
			return decryptedFilename.decode("utf-8")

	def decryptStreamChunk(self, response, wfile, chunkSize=24 * 1024, startOffset=0):
		origSize = struct.unpack("<Q", response.read(struct.calcsize("Q")))[0]
		decryptor = AES.new(self.key, AES.MODE_ECB)
		count = 0

		while chunk := response.read(chunkSize):
			count += 1
			decryptedChunk = decryptor.decrypt(chunk)

			if count == 1 and startOffset != 0:
				wfile.write(decryptedChunk[startOffset:])
			elif len(chunk) < len(decryptedChunk.strip()):
				wfile.write(decryptedChunk.strip())
			else:
				wfile.write(decryptedChunk)

	def decryptString(self, stringEncrypted):
		decryptor = AES.new(self.key, AES.MODE_ECB)

		if len(stringEncrypted) == 0:
			return

		try:
			return decryptor.decrypt(base64.b64decode(stringEncrypted.replace("---", "/").encode("utf-8"))).rstrip()
		except Exception:
			return

	def encryptFile(self, inFilename, outFilename=None, chunkSize=64 * 1024):
		""" Encrypts a file using AES (CBC mode) with the
			given key.

			key:
				The encryption key - a string that must be
				either 16, 24 or 32 bytes long. Longer keys
				are more secure.

			inFilename:
				Name of the input file

			outFilename:
				If None, '<inFilename>.enc' will be used.

			chunkSize:
				Sets the size of the chunk which the function
				uses to read and encrypt the file. Larger chunk
				sizes can be faster for some files and machines.
				chunksize must be divisible by 16.
		"""

		if not outFilename:
			outFilename = inFilename + ".enc"

		# key = _generateKey(key, salt, NUMBER_OF_ITERATIONS)
		# iv = "".join(chr(random.randint(0, 0xFF)) for i in range(16))
		encryptor = AES.new(self.key, AES.MODE_ECB)
		fileSize = os.path.getsize(inFilename)

		with open(inFilename, "rb") as inFile:

			with open(outFilename, "wb") as outFile:
				outFile.write(struct.pack("<Q", fileSize))
				# outFile.write(iv)

				while True:
					chunk = inFile.read(chunkSize)

					if len(chunk) == 0:
						break
					elif len(chunk) % 16 != 0:
						chunk += b" " * (16 - len(chunk) % 16)

					outFile.write(encryptor.encrypt(chunk))

	def encryptFilename(filename):
		return base64.b64encode(filename)

	def encryptString(self, stringDecrypted):
		# key = _generateKey(key, salt, NUMBER_OF_ITERATIONS)
		# iv = "".join(chr(random.randint(0, 0xFF)) for i in range(16))
		encryptor = AES.new(self.key, AES.MODE_ECB)

		if len(stringDecrypted) == 0:
			return
		elif len(stringDecrypted) % 16 != 0:
			stringDecrypted += " " * (16 - len(stringDecrypted) % 16)

		return base64.b64encode(encryptor.encrypt(stringDecrypted.encode("utf-8"))).replace(b"/", b"---")

	def _generateKey(self, password, iterations=NUMBER_OF_ITERATIONS):

		if not iterations > 0:
			return

		key = password.encode("utf-8") + self.salt

		for i in range(iterations):
			key = hashlib.sha256(key).digest()

		return key

	def _generateSalt(self, size=SALT_SIZE):
		return "".join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(size)).encode("utf-8")

	def _setup(self, saltFile=None, saltPassword=None, settings=None):

		if settings:
			saltFile = settings.getSetting("crypto_salt")
			saltPassword = settings.getSetting("crypto_password")

		try:

			try:

				with open(saltFile, "rb") as salt:
					self.salt = salt.read()

			except Exception:

				with open(saltFile, "wb") as salt:
					self.salt = self._generateSalt()
					salt.write(self.salt)

		except Exception:
			return

		if saltPassword:
			self.key = self._generateKey(saltPassword)

from .xsalsa20 import xsalsa20open
from .utils import byte_increment, nonce_add, nonce_increment

NONCE_SIZE = 24
BLOCK_SIZE = 64 * 1024
MAGIC_HEADER_SIZE = 8
BLOCK_HEADER_SIZE = 16


class File:

	def __init__(self, key):
		self.key = key
		self.nonce = None

	def decryptStream(self, response, filePath):

		if response.read(MAGIC_HEADER_SIZE) != b"RCLONE\x00\x00":
			return

		chunkSize = BLOCK_SIZE + BLOCK_HEADER_SIZE
		nonce = response.read(NONCE_SIZE)

		with open(filePath, "wb") as outFile:

			while chunk := response.read(chunkSize):
				outFile.write(self._decryptBytes(chunk, nonce, chunkSize))
				nonce = nonce_increment(nonce)

	def decryptStreamChunk(self, response, wfile, blockIndex, blockOffset):
		chunkSize = BLOCK_SIZE + BLOCK_HEADER_SIZE

		if blockOffset:
			nonce = self.nonce
			nonce = nonce_add(nonce, blockIndex)
		else:
			header = response.read(MAGIC_HEADER_SIZE)
			nonce = response.read(NONCE_SIZE)

			if not self.nonce:
				self.nonce = nonce

		while chunk := response.read(chunkSize):
			decryptedChunk = self._decryptBytes(chunk, nonce, chunkSize)

			if blockOffset:
				decryptedChunk = decryptedChunk[blockOffset:]
				blockOffset = 0

			wfile.write(decryptedChunk)
			nonce = nonce_increment(nonce)

	def _decryptBytes(self, inputBytes, nonce, chunkSize):

		if inputBytes == b"":
			return b""

		outputBytes = b""
		blockNum = len(inputBytes) // chunkSize
		bytesRemain = len(inputBytes) % chunkSize

		for i in range(blockNum):
			pos = i * chunkSize
			outputBytes += xsalsa20open(inputBytes[pos:pos + chunkSize], nonce, self.key)
			nonce = nonce_increment(nonce)

		if bytesRemain != 0:
			outputBytes += xsalsa20open(inputBytes[blockNum * chunkSize:], nonce, self.key)

		return outputBytes

from .xsalsa20 import secretbox_xsalsa20_open

MAGIC_HEADER_SIZE = 8
NONCE_SIZE = 24
BLOCK_HEADER_SIZE = 16
BLOCK_SIZE = 64 * 1024

def byte_increment(byte: int) -> int:

	if (byte > 255):
		raise ValueError("Byte must be in range(0, 256)")

	return (byte + 1) if (byte < 255) else 0

def nonce_increment(nonce: bytes, start: int = 0) -> bytes:
	nonce_array = bytearray(nonce)

	for i in range(start, len(nonce)):
		digit = nonce_array[i]
		newDigit = byte_increment(digit)
		nonce_array[i] = newDigit

		if newDigit >= digit:
			break

	return bytes(nonce_array)

def nonce_add(nonce: bytes, x: int) -> bytes:

	if len(nonce) < 8:
		raise ValueError("The length of nonce should greater than 8")

	if x <= 0:
		return nonce

	nonce_array = bytearray(nonce)
	carry = 0

	for i in range(8):
		digit = nonce_array[i]
		xDigit = x & 255
		x = x >> 8
		carry = carry + (digit & 65535) + (xDigit & 65535)
		nonce_array[i] = carry & 255
		carry = carry >> 8

	newNonce = bytes(nonce_array)

	if not carry == 0:
		newNonce = nonce_increment(newNonce, 8)

	return newNonce

class File:

	def __init__(self, key):
		self.key = key
		self.nonce = None

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

	def decryptStream(self, response, filePath):

		if response.read(MAGIC_HEADER_SIZE) != b"RCLONE\x00\x00":
			return

		chunkSize = BLOCK_SIZE + BLOCK_HEADER_SIZE
		nonce = response.read(NONCE_SIZE)

		with open(filePath, "wb") as outFile:

			while chunk := response.read(chunkSize):
				outFile.write(self._decryptBytes(chunk, nonce, chunkSize))
				nonce = nonce_increment(nonce)

	def _decryptBytes(self, inputBytes, nonce, chunkSize):

		if inputBytes == b"":
			return b""

		outputBytes = b""
		blockNum = len(inputBytes) // chunkSize
		bytesRemain = len(inputBytes) % chunkSize

		for i in range(blockNum):
			pos = i * chunkSize
			outputBytes += secretbox_xsalsa20_open(inputBytes[pos:pos + chunkSize], nonce, self.key)
			nonce = nonce_increment(nonce)

		if bytesRemain != 0:
			outputBytes += secretbox_xsalsa20_open(inputBytes[blockNum * chunkSize:], nonce, self.key)

		return outputBytes

"""
References:
https://github.com/fweinb/rclone-js/blob/master/src/ciphers/eme/index.js
https://github.com/rfjakob/eme/blob/master/eme.go
"""

DIRECTION_ENCRYPT = 0
DIRECTION_DECRYPT = 1


# multByTwo - GF multiplication as specified in the EME-32 draft
def multByTwo(out_bytes: bytes) -> bytes:

	if not len(out_bytes) == 16:
		raise ValueError("Invalid length")

	last = out_bytes[0]
	out_byte_array = bytearray([0] * 16)
	out_byte_array[0] = (2 * out_bytes[0]) & 0xff

	if out_bytes[15] >= 128:
		out_byte_array[0] = out_byte_array[0] ^ 135

	for i in range(1, 16):
		tmp = out_bytes[i]
		out_byte_array[i] = (2 * out_bytes[i]) & 0xff

		if last >= 128:
			out_byte_array[i] = (out_byte_array[i] + 1) & 0xff

		last = tmp

	return bytes(out_byte_array)


def xorBlocks(out_bytes: bytes, in1: bytes, in2: bytes) -> bytes:

	if (not len(in1) == len(in2)) and (not len(in2) == len(out_bytes)):
		raise ValueError("Length mismatch")

	out_byte_array = bytearray(out_bytes)

	for i in range(len(in1)):
		out_byte_array[i] = in1[i] ^ in2[i]

	return bytes(out_byte_array)


# tabulateL - calculate L_i for messages up to a length of m cipher blocks
def tabulateL(bc, m: int) -> list:
	Li = bc.encrypt(b"\x00" * 16)
	LTable = [None] * m

	for i in range(m):
		Li = multByTwo(Li)
		LTable[i] = Li

	return LTable


# aesTransform - encrypt or decrypt (according to "direction") using block
def aesTransform(src: bytes, directon: int, bc) -> bytes:

	if directon == DIRECTION_ENCRYPT:
		return bc.encrypt(src)
	elif directon == DIRECTION_DECRYPT:
		return bc.decrypt(src)


def transform(bc, tweak: bytes, inputData: bytes, direction: int) -> bytes:
	# In the paper, the tweak is just called "T". Call it the same here to
	# make following the paper easy.
	T = tweak
	# In the paper, the plaintext data is called "P" and the ciphertext is
	# called "C". Because encryption and decryption are virtually identical,
	# we share the code and always call the input data "P" and the output data
	# "c", regardless of the direction.
	P = inputData

	if not len(T) == 16:
		raise ValueError("Tweak must be 16 bytes")

	if not len(P) % 16 == 0:
		raise ValueError("Input Data must be a multiple of 16")

	m = int(len(P) / 16)

	if m == 0 or m > 128:
		raise ValueError(f"EME operates on 1 to 128 block-cipher blocks, you passed {m}")

	c = bytearray([0] * len(P))
	LTable = tabulateL(bc, m)
	PPj = bytearray([0] * 16)

	for i in range(m):
		Pj = P[i * 16 : (i + 1) * 16]
		# PPj = 2**(j-1)*L xor Pj
		PPj = xorBlocks(PPj, Pj, LTable[i])
		# PPPj = AESenc(K; PPj)
		tmp = aesTransform(PPj, direction, bc)
		c[i * 16 : len(tmp) + i * 16] = tmp

	# MP =(xorSum PPPj) xor T
	mp = bytearray([0] * 16)
	mp = xorBlocks(mp, c[0 : 16], T)

	for i in range(1, m):
		mp = xorBlocks(mp, mp, c[i * 16 : (i + 1) * 16])

	# MC = AESenc(K; MP)
	mc = aesTransform(mp, direction, bc)
	# M = MP xor MC
	m_ = bytearray([0] * 16)
	m_ = xorBlocks(m_, mp, mc)
	cccj = bytearray([0] * 16)

	for i in range(1, m):
		m_ = multByTwo(m_)
		# CCCj = 2**(j-1)*M xor PPPj
		cccj = xorBlocks(cccj, c[i * 16 : (i + 1) * 16], m_)
		c[i * 16 : len(cccj) + i * 16] = cccj

	# CCC1 = (xorSum CCCj) xor T xor MC
	ccc1 = bytearray([0] * 16)
	ccc1 = xorBlocks(ccc1, mc, T)

	for i in range(1, m):
		ccc1 = xorBlocks(ccc1, ccc1, c[i * 16 : (i + 1) * 16])

	c[0: len(ccc1)] = ccc1

	for i in range(m):
		# CCj = AES-enc(K; CCCj)
		tmp = aesTransform(c[i * 16 : (i + 1) * 16], direction, bc)
		c[i * 16 : len(tmp) + i * 16] = tmp
		# Cj = 2**(j-1)*L xor CCj
		tmp = c[i * 16 : (i + 1) * 16]
		tmp = xorBlocks(tmp, tmp, LTable[i])
		c[i * 16 : len(tmp) + i * 16] = tmp

	return bytes(c)


def encrypt(bc, tweak: bytes, data: bytes) -> bytes:
	"""
	:param bc:
	\n
	``from Crypto.Cipher import AES``
	\n
	``bc = AES.new(nameKey, mode = AES.MODE_ECB)``
	"""
	return transform(bc, tweak, data, DIRECTION_ENCRYPT)


def decrypt(bc, tweak: bytes, data: bytes) -> bytes:
	"""
	:param bc:
	\n
	``from Crypto.Cipher import AES``
	\n
	``bc = AES.new(nameKey, mode = AES.MODE_ECB)``
	"""
	return transform(bc, tweak, data, DIRECTION_DECRYPT)

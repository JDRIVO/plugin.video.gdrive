import struct
from functools import partial

try:
	from Cryptodome.Util.strxor import strxor
except ImportError:
	from Crypto.Util.strxor import strxor

O = struct.unpack("<4I", b"expand 32-byte k")
unpack_2I = partial(struct.unpack, "<2I")
unpack_4I = partial(struct.unpack, "<4I")
unpack_8I = partial(struct.unpack, "<8I")
pack_8I = partial(struct.pack, "<8I")
pack_16I = partial(struct.pack, "<16I")


def xsalsa20open(c, n, k):
	s = streamXsalsa20(16 + len(c), n, k)
	return strxor(c[16:], s[32:])


def rotate(x, n):
	x &= 0xffffffff
	return ((x << n) | (x >> (32 - n))) & 0xffffffff


def doubleRound(s):
	s[4] ^= rotate(s[0] + s[12], 7); s[8] ^= rotate(s[4] + s[0], 9)
	s[12] ^= rotate(s[8] + s[4], 13); s[0] ^= rotate(s[12] + s[8], 18)
	s[9] ^= rotate(s[5] + s[1], 7); s[13] ^= rotate(s[9] + s[5], 9)
	s[1] ^= rotate(s[13] + s[9], 13); s[5] ^= rotate(s[1] + s[13], 18)
	s[14] ^= rotate(s[10] + s[6], 7); s[2] ^= rotate(s[14] + s[10], 9)
	s[6] ^= rotate(s[2] + s[14], 13); s[10] ^= rotate(s[6] + s[2], 18)
	s[3] ^= rotate(s[15] + s[11], 7); s[7] ^= rotate(s[3] + s[15], 9)
	s[11] ^= rotate(s[7] + s[3], 13); s[15] ^= rotate(s[11] + s[7], 18)
	s[1] ^= rotate(s[0] + s[3], 7); s[2] ^= rotate(s[1] + s[0], 9)
	s[3] ^= rotate(s[2] + s[1], 13); s[0] ^= rotate(s[3] + s[2], 18)
	s[6] ^= rotate(s[5] + s[4], 7); s[7] ^= rotate(s[6] + s[5], 9)
	s[4] ^= rotate(s[7] + s[6], 13); s[5] ^= rotate(s[4] + s[7], 18)
	s[11] ^= rotate(s[10] + s[9], 7); s[8] ^= rotate(s[11] + s[10], 9)
	s[9] ^= rotate(s[8] + s[11], 13); s[10] ^= rotate(s[9] + s[8], 18)
	s[12] ^= rotate(s[15] + s[14], 7); s[13] ^= rotate(s[12] + s[15], 9)
	s[14] ^= rotate(s[13] + s[12], 13); s[15] ^= rotate(s[14] + s[13], 18)


def rounds(s, n, add=True):

	if add:
		s1 = [*s]

	[doubleRound(s) for _ in range(n // 2)]

	if add:

		for i in range(16):
			s[i] = (s[i] + s1[i]) & 0xffffffff


def block(n, k):
	s = [0] * 16
	s[0::5], s[1:5], s[6:10], s[11:15] = O, k[:4], n, k[4:]
	rounds(s, 20)
	return pack_16I(*s)


def hblock(n, k):
	s = [0] * 16
	s[0::5], s[1:5], s[6:10], s[11:15] = O, k[:4], n, k[4:]
	rounds(s, 20, False)
	return pack_8I(*(s[0::5] + s[6:10]))


def coreHsalsa20(n, k):
	return hblock(unpack_4I(n), unpack_8I(k))


def streamSalsa20(l, n, k):
	n = unpack_2I(n)
	k = unpack_8I(k)
	blocks = (l + 63) // 64
	output = bytearray(blocks * 64)

	for i in range(blocks):
		nList = (n[0], n[1], i, 0)
		output[i * 64:(i + 1) * 64] = block(nList, k)

	return output[:l]


def streamXsalsa20(l, n, k):
	return streamSalsa20(l, n[16:], coreHsalsa20(n[:16], k))

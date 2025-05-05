def byte_increment(byte: int) -> int:

	if byte > 255:
		raise ValueError("Byte must be in range(0, 256)")

	return byte + 1 if byte < 255 else 0


def nonce_add(nonce: bytes, x: int) -> bytes:

	if len(nonce) < 8:
		raise ValueError("Nonce length must be greater than 8")

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


def nonce_increment(nonce: bytes, start: int = 0) -> bytes:
	nonce_array = bytearray(nonce)

	for i in range(start, len(nonce)):
		digit = nonce_array[i]
		newDigit = byte_increment(digit)
		nonce_array[i] = newDigit

		if newDigit >= digit:
			break

	return bytes(nonce_array)

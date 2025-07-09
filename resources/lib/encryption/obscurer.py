import os
import base64

try:
	from Cryptodome.Cipher import AES
except ImportError:
	from Crypto.Cipher import AES

KEY = b"\x4a\x7e\x91\x23\xbd\x05\x67\xcf\x12\x9a\xee\x34\x58\xf0\x1b\xad\x76\x3c\x89\xdb\x45\x02\xe8\x9f\xca\x56\x71\x0d\x93\xbf\x24\x8e"
NONCE = b""
IV_SIZE = 16


def obscure(data: str) -> bytes:
	iv = os.urandom(IV_SIZE)

	try:
		crypter = AES.new(key=KEY, mode=AES.MODE_CTR, initial_value=iv, nonce=NONCE)
		encrypted = iv + crypter.encrypt(data.encode("utf-8"))
		encoded = base64.urlsafe_b64encode(encrypted)
		return encoded.rstrip(b"=")
	except Exception:
		raise ValueError("Failed to obscure data")


def unobscure(data: bytes) -> str:

	try:
		padded = data + b"=" * (-len(data) % 4)
		decoded = base64.urlsafe_b64decode(padded)
		iv = decoded[:IV_SIZE]
		ciphertext = decoded[IV_SIZE:]
		crypter = AES.new(key=KEY, mode=AES.MODE_CTR, initial_value=iv, nonce=NONCE)
		return crypter.decrypt(ciphertext).decode("utf-8")
	except Exception:
		raise ValueError("Failed to unobscure data")

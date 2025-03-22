import base64

try:
	from Cryptodome.Cipher import AES
	from Cryptodome.Protocol.KDF import scrypt
except:
	from Crypto.Cipher import AES
	from Crypto.Protocol.KDF import scrypt

from .file_cipher import File
from .name_cipher import Name

DEFAULT_SALT = b"\xA8\x0D\xF4\x3A\x8F\xBD\x03\x08\xA7\xCA\xB8\x3E\x58\x1F\x86\xB1"
PASSWD_CRYPT_KEY = b"\x9c\x93\x5b\x48\x73\x0a\x55\x4d\x6b\xfd\x7c\x63\xc8\x86\xa9\x2b\xd3\x90\x19\x8e\xb8\x12\x8a\xfb\xf4\xde\x16\x2b\x8b\x95\xf6\x38"
KEY_SIZE = 32 + 32 + 16


def unobscurePassword(self, password: bytes) -> bytes:

	if not password:
		return b""

	paddingNum = 4 - len(password) % 4
	password += b"=" * paddingNum

	try:
		password = base64.urlsafe_b64decode(password)
		crypter = AES.new(key=PASSWD_CRYPT_KEY, mode=AES.MODE_CTR, initial_value=password[:16], nonce=b"")
		return crypter.decrypt(password[16:])
	except:
		raise ValueError("Failed to unobscure password")


class Crypt:

	def __init__(self, password: str, salt: str = DEFAULT_SALT, passwordObscured: bool = False, nameEncoding: str = "base32") -> None:

		if isinstance(password, str):
			password = password.encode("utf-8")

		if passwordObscured:
			password = unobscurePassword(password)

		if isinstance(salt, str):
			salt = salt.encode("utf-8")

		if passwordObscured and salt != DEFAULT_SALT:
			salt = unobscurePassword(salt)

		key = scrypt(password, salt, KEY_SIZE, 16384, 8, 1)
		nameKey = key[32:64]
		nameTweak = key[64:]
		cipher = AES.new(nameKey, AES.MODE_ECB)
		self.File = File(key[:32])
		self.Name = Name(nameKey, nameTweak, cipher, nameEncoding)

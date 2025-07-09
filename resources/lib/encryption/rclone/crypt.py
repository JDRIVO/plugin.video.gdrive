try:
	from Cryptodome.Cipher import AES
	from Cryptodome.Protocol.KDF import scrypt
except ImportError:
	from Crypto.Cipher import AES
	from Crypto.Protocol.KDF import scrypt

from .file_cipher import File
from .name_cipher import Name

DEFAULT_SALT = "\xA8\x0D\xF4\x3A\x8F\xBD\x03\x08\xA7\xCA\xB8\x3E\x58\x1F\x86\xB1"
KEY_SIZE = 80


class Crypt:

	def __init__(self, password: str, salt: str = DEFAULT_SALT, nameEncoding: str = "base32") -> None:
		key = scrypt(password.encode("utf-8"), salt.encode("utf-8"), KEY_SIZE, 16384, 8, 1)
		nameKey = key[32:64]
		nameTweak = key[64:]
		cipher = AES.new(nameKey, AES.MODE_ECB)
		self.file = File(key[:32])
		self.name = Name(nameKey, nameTweak, cipher, nameEncoding)

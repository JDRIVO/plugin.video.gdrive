import secrets
from dataclasses import dataclass, field

from .encryption_types import EncryptionType


@dataclass
class EncryptionProfile:
	id: str = field(default_factory=lambda: secrets.token_hex(6))
	name: str = ""
	password: str = ""
	salt: str = ""
	encryptData: bool = True
	encryptDirNames: bool = True


@dataclass
class GDriveEncryptionProfile(EncryptionProfile):
	type = EncryptionType.GDRIVE


@dataclass
class RcloneEncryptionProfile(EncryptionProfile):
	type = EncryptionType.RCLONE
	filenameEncryption: str = "standard"
	filenameEncoding: str = "base32"
	suffix: str = ".bin"

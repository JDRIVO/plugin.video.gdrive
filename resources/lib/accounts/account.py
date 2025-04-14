from ..encryption.obscurer import obscure, unobscure


class BaseAccount:

	def __init__(self):
		self.name = None
		self._accessToken = None
		self.tokenExpiry = None
		self.driveStream = None

	@property
	def accessToken(self):
		return unobscure(self._accessToken)

	@accessToken.setter
	def accessToken(self, value):
		self._accessToken = obscure(value)


class OAuthAccount(BaseAccount):

	def __init__(self):
		super().__init__()
		self.type = "oauth"
		self._clientID = None
		self._clientSecret = None
		self._refreshToken = None

	@property
	def clientID(self):
		return unobscure(self._clientID)

	@clientID.setter
	def clientID(self, value):
		self._clientID = obscure(value)

	@property
	def clientSecret(self):
		return unobscure(self._clientSecret)

	@clientSecret.setter
	def clientSecret(self, value):
		self._clientSecret = obscure(value)

	@property
	def refreshToken(self):
		return unobscure(self._refreshToken)

	@refreshToken.setter
	def refreshToken(self, value):
		self._refreshToken = obscure(value)


class ServiceAccount(BaseAccount):

	def __init__(self):
		super().__init__()
		self.type = "service"
		self._key = None
		self._email = None

	@property
	def email(self):
		return unobscure(self._email)

	@email.setter
	def email(self, value):
		self._email = obscure(value)

	@property
	def key(self):
		return unobscure(self._key)

	@key.setter
	def key(self, value):
		self._key = obscure(value)


class Account:
	name = None
	clientID = None
	clientSecret = None
	accessToken = None
	refreshToken = None
	expiry = None
	driveStream = None
	key = None
	email = None

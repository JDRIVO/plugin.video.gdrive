from .account import OAuthAccount, ServiceAccount


def convert(accountData):

	for driveID, data in accountData["drives"].items():
		newAccounts = []

		for account in data["accounts"]:

			if account.key:
				newAccount = ServiceAccount()
				newAccount.key = account.key
				newAccount.email = account.email
			else:
				newAccount = OAuthAccount()
				newAccount.clientID = account.clientID
				newAccount.clientSecret = account.clientSecret
				newAccount.refreshToken = account.refreshToken

			newAccount.name = account.name
			newAccount.accessToken = account.accessToken
			newAccount.tokenExpiry = account.expiry
			newAccounts.append(newAccount)

		data["accounts"] = newAccounts

	accountData["version"] = 2
	return accountData

import os
import pickle
import xbmcvfs
import xbmcaddon

ADDON_PATH = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo("profile"))

if not os.path.exists(ADDON_PATH):
	os.mkdir(ADDON_PATH)

ACCOUNTS_FILE = os.path.join(ADDON_PATH, "accounts.pkl")


class AccountManager:

	def __init__(self, settings):
		self.settings = settings
		self.loadAccounts()

	def loadAccounts(self):

		try:
			self.accountData = self.loadFile()
			self.accounts = self.accountData["drives"]
			self.aliases = self.accountData["aliases"]
		except Exception:
			self.accountData = {
				"aliases": {},
				"drives": {},
			}
			self.accounts = self.accountData["drives"]
			self.aliases = self.accountData["aliases"]

	@staticmethod
	def loadFile(filePath=ACCOUNTS_FILE):

		with open(filePath, "rb") as accounts:
			return pickle.load(accounts)

	def getAccount(self, driveID):
		accounts = self.accounts.get(driveID)

		if accounts:
			# avoid returning a service account
			return [account for account in accounts["accounts"] if not account.key][0]

	def getAccounts(self, driveID):
		return self.accounts[driveID]["accounts"]

	def saveAccounts(self, filePath=ACCOUNTS_FILE):

		with open(filePath, "wb") as accounts:
			pickle.dump(self.accountData, accounts)

	def addAccount(self, account, driveID):
		accounts = self.accounts.get(driveID)

		if accounts:
			accounts["accounts"].insert(0, account)
		else:
			self.accounts.update(
				{
					driveID: {
						"accounts": [account],
						"alias": "",
					}
				}
			)

		self.saveAccounts()

	def renameAccount(self, driveID, accountIndex, newAccountName):
		self.accounts[driveID]["accounts"][accountIndex].name = newAccountName
		self.saveAccounts()

	def deleteAccount(self, driveID, account):
		self.accounts[driveID]["accounts"].remove(account)

		if not self.accounts[driveID]:
			self.deleteDrive(driveID)
		else:
			self.saveAccounts()

	def deleteAccounts(self, indexes, accounts, driveID):

		for index in sorted(indexes, reverse=True):
			del accounts[index]

		if not self.accounts[driveID]["accounts"]:
			self.deleteDrive(driveID)
		else:
			self.saveAccounts()

	def deleteDrive(self, driveID):
		del self.accounts[driveID]
		self.saveAccounts()

	@staticmethod
	def getAccountNames(accounts):
		return [account.name for account in accounts]

	def mergeAccounts(self, filePath):

		try:
			importedAccounts = self.loadFile(filePath)
		except Exception:
			return "failed"

		if not self.accounts:
			self.accounts = importedAccounts
		else:

			for driveID, data in importedAccounts["drives"].items():

				if driveID not in self.accounts:
					self.accounts.update(
						{
							driveID: {
								"accounts": data["accounts"],
								"alias": "",
							}
						}
					)
				else:
					currentAccounts = self.accounts[driveID]["accounts"]

					for account in data["accounts"]:

						if account not in currentAccounts:
							currentAccounts.append(account)

		self.saveAccounts()

	def exportAccounts(self, filePath):
		self.saveAccounts(os.path.join(filePath, "gdrive_accounts.pkl"))

	def getDrives(self):
		return [[driveID, data["alias"] if data["alias"] else driveID] for driveID, data in self.accounts.items()]

	def getAlias(self, driveID):
		return self.accounts[driveID]["alias"]

	def setAlias(self, driveID, alias):
		self.aliases[alias] = driveID
		self.accounts[driveID]["alias"] = alias
		self.saveAccounts()

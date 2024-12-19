import os

from constants import ADDON_PATH
from ..filesystem.file_operations import FileOperations

if not os.path.exists(ADDON_PATH):
	os.mkdir(ADDON_PATH)

ACCOUNTS_FILE = os.path.join(ADDON_PATH, "accounts.pkl")


class AccountManager:

	def __init__(self):
		self.fileOperations = FileOperations()
		self.setAccounts()

	def addAccount(self, account, driveID):
		accounts = self.accounts.get(driveID)

		if accounts:
			accounts["accounts"].insert(0, account)
		else:
			self.accounts.update({driveID: {"accounts": [account], "alias": ""}})

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
		self.setAccounts()

		if not self.accounts.get(driveID):
			return

		alias = self.getAlias(driveID)

		if alias:
			del self.aliases[alias]

		del self.accounts[driveID]
		self.saveAccounts()

	def exportAccounts(self, filePath):
		self.saveAccounts(filePath)

	def getAccount(self, driveID):
		accounts = self.accounts.get(driveID)

		if not accounts:
			return

		accounts = accounts.get("accounts")

		if not accounts:
			return

		# avoid returning a service account
		accounts = [account for account in accounts if not account.key]

		if accounts:
			return accounts[0]

	@staticmethod
	def getAccountNames(accounts):
		return sorted([account.name for account in accounts], key=lambda x: x.lower())

	def getAccounts(self, driveID):
		return self.accounts[driveID]["accounts"]

	def getAlias(self, driveID):
		return self.accounts[driveID]["alias"]

	def getDrives(self):
		return [[driveID, data["alias"] if data["alias"] else driveID] for driveID, data in self.accounts.items()]

	def mergeAccounts(self, filePath):
		accounts = self._loadAccounts(filePath)

		if not accounts:
			return

		if not self.accounts:
			self.accountData = accounts
		else:

			for driveID, data in accounts["drives"].items():

				if driveID not in self.accounts:
					self.accounts.update({driveID: {"accounts": data["accounts"], "alias": ""}})
				else:
					currentAccounts = self.accounts[driveID]["accounts"]

					for account in data["accounts"]:

						if account not in currentAccounts:
							currentAccounts.append(account)

		self.saveAccounts()
		return True

	def renameAccount(self, driveID, accountIndex, accountName):
		self.accounts[driveID]["accounts"][accountIndex].name = accountName
		self.saveAccounts()

	def saveAccounts(self, filePath=ACCOUNTS_FILE):
		self.fileOperations.savePickleFile(self.accountData, filePath)

	def setAccounts(self):
		self.accountData = self._loadAccounts()

		if self.accountData:
			self.accounts = self.accountData["drives"]
			self.aliases = self.accountData["aliases"]
		else:
			self.accountData = {"aliases": {}, "drives": {}}
			self.accounts = self.accountData["drives"]
			self.aliases = self.accountData["aliases"]

	def setAlias(self, driveID, alias):
		currentAlias = self.getAlias(driveID)

		if currentAlias:
			del self.aliases[currentAlias]

		self.aliases[alias] = driveID
		self.accounts[driveID]["alias"] = alias
		self.saveAccounts()

	def _loadAccounts(self, filePath=ACCOUNTS_FILE):
		return self.fileOperations.loadPickleFile(filePath)

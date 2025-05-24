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

		if not accounts:
			self.accounts.update({driveID: {"accounts": [account], "alias": ""}})
		else:
			accounts = accounts["accounts"]
			account.name = self._getUniqueAccountName(account.name, self.getAccountNames(accounts))
			accounts.insert(0, account)

		self.saveAccounts()

	def addAccounts(self, newAccounts, driveID):
		accounts = self.accounts.get(driveID)

		if not accounts:
			self.accounts.update({driveID: {"accounts": [account], "alias": ""}})
		else:
			accounts = accounts["accounts"]

		for account in newAccounts:
			account.name = self._getUniqueAccountName(account.name, self.getAccountNames(accounts))
			accounts.insert(0, account)

		self.saveAccounts()

	def deleteAccount(self, account, driveID):
		self.accounts[driveID]["accounts"].remove(account)

		if not self.accounts[driveID]:
			self.deleteDrive(driveID)
		else:
			self.saveAccounts()

	def deleteAccounts(self, deletedAccounts, accounts, driveID):
		self.accounts[driveID]["accounts"] = [account for account in accounts if account.name not in deletedAccounts]

		if not self.accounts[driveID]["accounts"]:
			self.deleteDrive(driveID)
		else:
			self.saveAccounts()

	def deleteDrive(self, driveID):
		self.setAccounts()

		if driveID not in self.accounts:
			return

		if alias := self.getAlias(driveID):
			del self.aliases[alias]

		del self.accounts[driveID]
		self.saveAccounts()

	def getAccount(self, driveID, preferOauth=True):
		accounts = self.accounts.get(driveID, {}).get("accounts")

		if not accounts:
			return

		if preferOauth:
			return next((account for account in accounts if account.type == "oauth"), None)

		return next((account for account in accounts if account.type == "oauth"), None) or next(iter(accounts), None)

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
					accountNames = self.getAccountNames(currentAccounts)

					for account in data["accounts"]:

						if account not in currentAccounts:
							account.name = self._getUniqueAccountName(account.name, accountNames)
							currentAccounts.append(account)

		self.saveAccounts()
		return True

	def renameAccount(self, accountName, index, driveID):
		accounts = self.accounts[driveID]["accounts"]
		account = accounts[index]
		account.name = self._getUniqueAccountName(accountName, self.getAccountNames(accounts))
		self.saveAccounts()

	def saveAccounts(self, filePath=ACCOUNTS_FILE):
		self.fileOperations.savePickleFile(self.accountData, filePath)

	def setAccounts(self):
		self.accountData = self._loadAccounts()

		if not self.accountData:
			self.accountData = {"version": 2, "aliases": {}, "drives": {}}

		self.accounts = self.accountData["drives"]
		self.aliases = self.accountData["aliases"]

	def setAlias(self, alias, driveID):

		if currentAlias := self.getAlias(driveID):
			del self.aliases[currentAlias]

		self.aliases[alias] = driveID
		self.accounts[driveID]["alias"] = alias
		self.saveAccounts()

	@staticmethod
	def _getUniqueAccountName(accountName, accountNames):
		accountName_ = accountName
		copy = 1

		while accountName in accountNames:
			accountName = f"{accountName_} {copy}"
			copy += 1

		accountNames.append(accountName)
		return accountName

	def _loadAccounts(self, filePath=ACCOUNTS_FILE):
		return self.fileOperations.loadPickleFile(filePath)

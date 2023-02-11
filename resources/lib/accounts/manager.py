import os
import pickle
import xbmcvfs
import xbmcaddon

ACCOUNTS_FILE = os.path.join(xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo("path")), "accounts.pkl")


class AccountManager:

	def __init__(self, settings):
		self.settings = settings
		self.loadAccounts()

	def loadAccounts(self):

		if os.path.exists(ACCOUNTS_FILE):

			try:

				with open(ACCOUNTS_FILE, "rb") as accounts:
					self.accounts = pickle.load(accounts)

			except EOFError:
				self.accounts = {}

		else:
			self.accounts = {}

	def getAccount(self, driveID):
		accounts = self.accounts.get(driveID)

		if accounts:
			return [account for account in accounts][0]

	def getAccounts(self, driveID):
		return self.accounts[driveID]

	def saveAccounts(self):

		with open(ACCOUNTS_FILE, "wb") as accounts:
			pickle.dump(self.accounts, accounts)

	def addAccount(self, accountInfo, driveID):
		accounts = self.accounts.get(driveID)

		if accounts:
			accounts.insert(0, accountInfo)
		else:
			self.accounts[driveID] = [accountInfo]

		self.saveAccounts()

	def renameAccount(self, driveID, accountIndex, newAccountName):
		self.accounts[driveID][accountIndex].name = newAccountName
		self.saveAccounts()

	def deleteAccount(self, driveID, account):
		self.accounts[driveID].remove(account)

		if not self.accounts[driveID]:
			self.deleteDrive(driveID)
		else:
			self.saveAccounts()

	def deleteAccounts(self, indexes, accounts, driveID):

		for index in sorted(indexes, reverse=True):
			del accounts[index]

		if not self.accounts[driveID]:
			self.deleteDrive(driveID)
		else:
			self.saveAccounts()

	def deleteDrive(self, driveID):
		del self.accounts[driveID]
		self.saveAccounts()

	@staticmethod
	def getAccountNames(accounts):
		return [account.name for account in accounts]

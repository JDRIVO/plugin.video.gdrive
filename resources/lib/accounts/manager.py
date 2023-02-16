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

		try:
			self.accounts = self.loadFile()
		except Exception:
			self.accounts = {}

	@staticmethod
	def loadFile(filePath=ACCOUNTS_FILE):

		with open(filePath, "rb") as accounts:
			return pickle.load(accounts)

	def getAccount(self, driveID):
		accounts = self.accounts.get(driveID)

		if accounts:
			# avoid returning a service account
			return [account for account in accounts if not account.key][0]

	def getAccounts(self, driveID):
		return self.accounts[driveID]

	def saveAccounts(self, filePath=ACCOUNTS_FILE):

		with open(filePath, "wb") as accounts:
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

	def mergeAccounts(self, filePath):

		try:
			importedAccounts = self.loadFile(filePath)
		except Exception:
			return "failed"

		if not self.accounts:
			self.accounts = importedAccounts
		else:

			for driveID, accounts in importedAccounts.items():

				if driveID not in self.accounts:
					self.accounts[driveID] = accounts
				else:
					currentAccounts = self.accounts[driveID]

					for account in accounts:

						if account not in currentAccounts:
							currentAccounts.append(account)

		self.saveAccounts()

	def exportAccounts(self, filePath):
		self.saveAccounts(os.path.join(filePath, "gdrive_accounts.pkl"))

	def getDrives(self):
		return [driveID for driveID in self.accounts]

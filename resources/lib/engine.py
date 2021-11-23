import re
import os
import sys
import time
import urllib
import xbmc
import xbmcgui
import xbmcplugin
import constants
from resources.lib import settings

PLUGIN_NAME = constants.PLUGIN_NAME
PLUGIN_HANDLE = int(sys.argv[1])
PLUGIN_URL = sys.argv[0]
ADDON = constants.addon
CLOUD_SERVICE = constants.cloudservice2
SETTINGS_MODULE = settings.Settings(ADDON)


class AccountActions:

	@staticmethod
	def getAccounts(accountAmount):
		accountNumbers, accountNames, accountInstances = [], [], []

		for count in range(1, accountAmount + 1):
			instanceName = PLUGIN_NAME + str(count)
			username = ADDON.getSetting(instanceName + "_username")

			if username:
				accountNumbers.append(str(count))
				accountNames.append(username)
				accountInstances.append(instanceName)

		return accountNumbers, accountNames, accountInstances

	@staticmethod
	def setDefault(instanceName):
		ADDON.setSetting("default_account", re.sub("[^\d]", "", instanceName))
		ADDON.setSetting("default_account_ui", ADDON.getSetting(instanceName + "_username"))

	@staticmethod
	def validateAccount(instanceName, accountName, userAgent):
		validation = CLOUD_SERVICE(PLUGIN_HANDLE, PLUGIN_URL, ADDON, instanceName, userAgent, SETTINGS_MODULE)
		validation.refreshToken()

		if not validation.failed:
			return True

	@staticmethod
	def renameAccount(instanceName, newName):
		accountName = ADDON.getSetting(instanceName + "_username")
		ADDON.setSetting(instanceName + "_username", newName)

		if ADDON.getSetting("default_account_ui") == accountName:
			ADDON.setSetting("default_account_ui", newName)

		fallbackAccounts = ADDON.getSetting("fallback_accounts_ui").split(", ")

		if accountName in fallbackAccounts:
			fallbackAccounts.remove(accountName)
			fallbackAccounts.append(newName)
			ADDON.setSetting("fallback_accounts_ui", ", ".join(fallbackAccounts))

	@staticmethod
	def deleteAccount(instanceName, fallbackAccountNames, fallbackAccountNumbers):
		accountName = ADDON.getSetting(instanceName + "_username")

		ADDON.setSetting(instanceName + "_username", "")
		ADDON.setSetting(instanceName + "_code", "")
		ADDON.setSetting(instanceName + "_client_id", "")
		ADDON.setSetting(instanceName + "_client_secret", "")
		ADDON.setSetting(instanceName + "_auth_access_token", "")
		ADDON.setSetting(instanceName + "_auth_refresh_token", "")

		if ADDON.getSetting("default_account_ui") == accountName:
			ADDON.setSetting("default_account_ui", "")
			ADDON.setSetting("default_account", "")

		if accountName in fallbackAccountNames:
			fallbackAccountNumbers.remove(re.sub("[^\d]", "", instanceName))
			fallbackAccountNames.remove(accountName)
			ADDON.setSetting("fallback_accounts", ",".join(fallbackAccountNumbers))
			ADDON.setSetting("fallback_accounts_ui", ", ".join(fallbackAccountNames))

	@staticmethod
	def fallbackModifier(instanceName, mode):
		fallbackAccountNumbers = ADDON.getSetting("fallback_accounts")
		fallbackAccountNames = ADDON.getSetting("fallback_accounts_ui")
		accountName = ADDON.getSetting(instanceName + "_username")
		accountNumber = re.sub("[^\d]", "", instanceName)

		if fallbackAccountNumbers:
			fallbackAccountNumbers = fallbackAccountNumbers.split(",")
			fallbackAccountNames = fallbackAccountNames.split(", ")

			if mode == "delete":
				fallbackAccountNumbers.remove(accountNumber)
				fallbackAccountNames.remove(accountName)
			else:
				fallbackAccountNumbers.append(accountNumber)
				fallbackAccountNames.append(accountName)

			ADDON.setSetting("fallback_accounts", ",".join(fallbackAccountNumbers))
			ADDON.setSetting("fallback_accounts_ui", ", ".join(fallbackAccountNames))
		else:
			ADDON.setSetting("fallback", "true")
			ADDON.setSetting("fallback_accounts", accountNumber)
			ADDON.setSetting("fallback_accounts_ui", accountName)


class ContentEngine:

	def addMenu(self, url, title, totalItems=0, instanceName=None):
		listitem = xbmcgui.ListItem(title)

		if instanceName is not None:
			cm = []
			cm.append((ADDON.getLocalizedString(30211), "Addon.OpenSettings({})".format(ADDON.getAddonInfo("id"))))
			listitem.addContextMenuItems(cm, True)

		xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, url, listitem, totalItems=totalItems)

	def run(self, dbID, dbType, filePath):
		mode = SETTINGS_MODULE.getParameter("mode", "main").lower()
		userAgent = SETTINGS_MODULE.getSetting("user_agent")
		accountAmount = ADDON.getSettingInt("account_amount")
		pluginQueries = settings.parseQuery(sys.argv[2][1:])
		accountActions = AccountActions()

		try:
			instanceName = (pluginQueries["instance"]).lower()
		except:
			instanceName = None

		if not instanceName and mode == "main":
			self.addMenu(PLUGIN_URL + "?mode=enroll", "[B]1. {}[/B]".format(ADDON.getLocalizedString(30207)), instanceName=True)
			self.addMenu(PLUGIN_URL + "?mode=fallback", "[B]2. {}[/B]".format(ADDON.getLocalizedString(30220)), instanceName=True)
			self.addMenu(PLUGIN_URL + "?mode=validate", "[B]3. {}[/B]".format(ADDON.getLocalizedString(30021)), instanceName=True)
			self.addMenu(PLUGIN_URL + "?mode=delete", "[B]4. {}[/B]".format(ADDON.getLocalizedString(30022)), instanceName=True)

			defaultAccount = ADDON.getSetting("default_account")
			fallBackAccounts = ADDON.getSetting("fallback_accounts").split(",")

			for count in range (1, accountAmount + 1):
				instanceName = PLUGIN_NAME + str(count)
				username = ADDON.getSetting(instanceName + "_username")

				if username:
					countStr = str(count)

					if countStr == defaultAccount:
						username = "[COLOR crimson][B]{}[/B][/COLOR]".format(username)
					elif countStr in fallBackAccounts:
						username = "[COLOR deepskyblue][B]{}[/B][/COLOR]".format(username)

					self.addMenu("{}?mode=main&instance={}".format(PLUGIN_URL, instanceName), username, instanceName=instanceName)

			xbmcplugin.setContent(PLUGIN_HANDLE, "files")
			xbmcplugin.addSortMethod(PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_LABEL)

		elif instanceName and mode == "main":
			fallbackAccounts = ADDON.getSetting("fallback_accounts").split(",")
			options = [
				ADDON.getLocalizedString(30219),
				ADDON.getLocalizedString(30002),
				ADDON.getLocalizedString(30023),
				ADDON.getLocalizedString(30159),
			]
			account = re.sub("[^\d]", "", instanceName)

			if account in fallbackAccounts:
				fallbackExists = True
				options.insert(0, ADDON.getLocalizedString(30212))
			else:
				fallbackExists = False
				options.insert(0, ADDON.getLocalizedString(30213))

			selection = xbmcgui.Dialog().contextmenu(options)

			if selection == 0:

				if fallbackExists:
					accountActions.fallbackModifier(instanceName, "delete")
				else:
					accountActions.fallbackModifier(instanceName, "add")

			elif selection == 1:
				accountActions.setDefault(instanceName)
			elif selection == 2:
				newName = xbmcgui.Dialog().input(ADDON.getLocalizedString(30002))

				if not newName:
					return

				accountActions.renameAccount(instanceName, newName)
			elif selection == 3:
				accountName = ADDON.getSetting(instanceName + "_username")
				validation = accountActions.validateAccount(instanceName, accountName, userAgent)

				if not validation:
					selection = xbmcgui.Dialog().yesno(ADDON.getLocalizedString(30000), "{} {}".format(accountName, ADDON.getLocalizedString(30019)))

					if selection:
						fallbackAccountNames = ADDON.getSetting("fallback_accounts_ui").split(", ")
						fallbackAccountNumbers = ADDON.getSetting("fallback_accounts").split(",")
						accountActions.deleteAccount(instanceName, fallbackAccountNames, fallbackAccountNumbers)
					else:
						return

				else:
					xbmcgui.Dialog().ok(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(30020))
					return

			elif selection == 4:
				selection = xbmcgui.Dialog().yesno(
					ADDON.getLocalizedString(30000),
					"{} {}?".format(
						ADDON.getLocalizedString(30121),
						ADDON.getSetting(instanceName + "_username"),
					)
				)

				if not selection:
					return

				fallbackAccountNames = ADDON.getSetting("fallback_accounts_ui").split(", ")
				fallbackAccountNumbers = ADDON.getSetting("fallback_accounts").split(",")
				accountActions.deleteAccount(instanceName, fallbackAccountNames, fallbackAccountNumbers)
			else:
				return

			xbmc.executebuiltin("Container.Refresh")

		elif mode == "enroll":
			import socket

			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.connect(("8.8.8.8", 80))
			address = s.getsockname()[0]
			s.close()

			selection = xbmcgui.Dialog().ok(
				ADDON.getLocalizedString(30000),
				"{} [B][COLOR blue]http://{}:{}/enroll[/COLOR][/B] {}".format(
					ADDON.getLocalizedString(30210),
					address,
					ADDON.getSetting("server_port"),
					ADDON.getLocalizedString(30218),
				)
			)

			if selection:
				xbmc.executebuiltin("Container.Refresh")

		elif mode == "make_default":
			accountActions.setDefault(instanceName)
			xbmc.executebuiltin("Container.Refresh")

		elif mode == "settings_default":
			accountNumbers, accountNames, accountInstances = accountActions.getAccounts(accountAmount)
			selection = xbmcgui.Dialog().select(ADDON.getLocalizedString(30120), accountNames)

			if selection == -1:
				return

			ADDON.setSetting("default_account", accountNumbers[selection])
			ADDON.setSetting("default_account_ui", accountNames[selection])
			xbmc.executebuiltin("Container.Refresh")

		elif mode == "fallback":
			accountNumbers, accountNames, accountInstances = accountActions.getAccounts(accountAmount)
			fallbackAccounts = ADDON.getSetting("fallback_accounts")
			fallbackAccountNames = ADDON.getSetting("fallback_accounts_ui")

			if fallbackAccounts:
				fallbackAccounts = [accountNumbers.index(x) for x in fallbackAccounts.split(",") if x in accountNumbers]
				selection = xbmcgui.Dialog().multiselect(ADDON.getLocalizedString(30120), accountNames, preselect=fallbackAccounts)
			else:
				selection = xbmcgui.Dialog().multiselect(ADDON.getLocalizedString(30120), accountNames)

			if not selection:
				return

			ADDON.setSetting("fallback_accounts", ",".join(accountNumbers[x] for x in selection))
			ADDON.setSetting("fallback_accounts_ui", ", ".join(accountNames[x] for x in selection))
			ADDON.setSetting("fallback", "true")
			xbmc.executebuiltin("Container.Refresh")

		elif mode == "validate":
			accountNumbers, accountNames, accountInstances = accountActions.getAccounts(accountAmount)
			accounts = [n for n in range(accountAmount)]
			selection = xbmcgui.Dialog().multiselect(ADDON.getLocalizedString(30024), accountNames, preselect=accounts)

			if not selection:
				return

			for index_ in selection:
				instanceName = accountInstances[index_]
				accountName = accountNames[index_]
				validation = accountActions.validateAccount(instanceName, accountName, userAgent)

				if not validation:
					selection = xbmcgui.Dialog().yesno(ADDON.getLocalizedString(30000), "{} {}".format(accountName, ADDON.getLocalizedString(30019)))

					if selection:
						fallbackAccountNames = ADDON.getSetting("fallback_accounts_ui").split(", ")
						fallbackAccountNumbers = ADDON.getSetting("fallback_accounts").split(",")
						accountActions.deleteAccount(instanceName, fallbackAccountNames, fallbackAccountNumbers)

			xbmcgui.Dialog().ok(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(30020))
			xbmc.executebuiltin("Container.Refresh")

		elif mode in ("delete", "settings_delete"):
			accountNumbers, accountNames, accountInstances = accountActions.getAccounts(accountAmount)
			selection = xbmcgui.Dialog().multiselect(ADDON.getLocalizedString(30158), accountNames)

			if not selection:
				return

			fallbackAccountNames = ADDON.getSetting("fallback_accounts_ui").split(", ")
			fallbackAccountNumbers = ADDON.getSetting("fallback_accounts").split(",")
			[accountActions.deleteAccount(accountInstances[x], fallbackAccountNames, fallbackAccountNumbers) for x in selection]

			if mode == "settings_delete":
				xbmcgui.Dialog().ok(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(30160))
			else:
				xbmcgui.Dialog().ok(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(30161))
				xbmc.executebuiltin("Container.Refresh")

		elif mode == "video":
			instanceName = PLUGIN_NAME + str(SETTINGS_MODULE.getSetting("default_account", 1))
			service = CLOUD_SERVICE(PLUGIN_HANDLE, PLUGIN_URL, ADDON, instanceName, userAgent, SETTINGS_MODULE)

			if service.failed:
				xbmcgui.Dialog().ok(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(30005))
				return

			if not SETTINGS_MODULE.cryptoPassword or not SETTINGS_MODULE.cryptoSalt:
				xbmcgui.Dialog().ok(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(30208))
				return

			try:
				service
			except NameError:
				xbmcgui.Dialog().ok(ADDON.getLocalizedString(30000), ADDON.getLocalizedString(30051) + " " + ADDON.getLocalizedString(30052))
				xbmc.log(ADDON.getLocalizedString(30051) + PLUGIN_NAME + "-login", xbmc.LOGERROR)
				return

			if (not dbID or not dbType) and not filePath:
				timeEnd = time.time() + 1

				while time.time() < timeEnd and (not dbID or not dbType):
					xbmc.executebuiltin("Dialog.Close(busydialog)")
					dbID = xbmc.getInfoLabel("ListItem.DBID")
					dbType = xbmc.getInfoLabel("ListItem.DBTYPE")

			if dbID:

				if dbType == "movie":
					jsonQuery = xbmc.executeJSONRPC(
						'{"jsonrpc": "2.0", "id": "1", "method": "VideoLibrary.GetMovieDetails", "params": {"movieid": %s, "properties": ["resume"]}}'
						% dbID
					)
					jsonKey = "moviedetails"
				else:
					jsonQuery = xbmc.executeJSONRPC(
						'{"jsonrpc": "2.0", "id": "1", "method": "VideoLibrary.GetEpisodeDetails", "params": {"episodeid": %s, "properties": ["resume"]}}'
						% dbID
					)
					jsonKey = "episodedetails"

				import json

				jsonResponse = json.loads(jsonQuery.encode("utf-8"))

				try:
					resumeData = jsonResponse["result"][jsonKey]["resume"]
				except:
					return

				resumePosition = resumeData["position"]
				videoLength = resumeData["total"]

			elif filePath:
				from sqlite3 import dbapi2 as sqlite

				dbPath = xbmc.translatePath(SETTINGS_MODULE.getSetting("video_db"))
				db = sqlite.connect(dbPath)
				dirPath = os.path.dirname(filePath) + os.sep
				fileName = os.path.basename(filePath)
				resumePosition = list(
					db.execute(
						"SELECT timeInSeconds FROM bookmark WHERE idFile=(SELECT idFile FROM files WHERE idPath=(SELECT idPath FROM path WHERE strPath=?) AND strFilename=?)",
						(dirPath, fileName)
					)
				)

				if resumePosition:
					resumePosition = resumePosition[0][0]
					videoLength = list(
						db.execute(
							"SELECT totalTimeInSeconds FROM bookmark WHERE idFile=(SELECT idFile FROM files WHERE idPath=(SELECT idPath FROM path WHERE strPath=?) AND strFilename=?)",
							(dirPath, fileName)
						)
					)[0][0]
				else:
					resumePosition = 0

			else:
				resumePosition = 0

				# import pickle

				# resumeDBPath = xbmc.translatePath(SETTINGS_MODULE.resumeDBPath)
				# resumeDB = os.path.join(resumeDBPath, "kodi_resumeDB.p")

				# try:
					# with open(resumeDB, "rb") as dic:
						# videoData = pickle.load(dic)
				# except:
					# videoData = {}

				# try:
					# resumePosition = videoData[filename]
				# except:
					# videoData[filename] = 0
					# resumePosition = 0

				# strmName = SETTINGS_MODULE.getParameter("title") + ".strm"
				# cursor = list(db.execute("SELECT timeInSeconds FROM bookmark WHERE idFile=(SELECT idFile FROM files WHERE strFilename='%s')" % strmName))

				# if cursor:
					# resumePosition = cursor[0][0]
				# else:
					# resumePosition = 0

			resumeOption = False

			if resumePosition > 0:
				options = ("Resume from " + str(time.strftime("%H:%M:%S", time.gmtime(resumePosition))), "Play from beginning")
				selection = xbmcgui.Dialog().contextmenu(options)

				if selection == 0:
					# resumePosition = resumePosition / total * 100
					resumeOption = True
				# elif selection == 1:
					# resumePosition = "0"
					# videoData[filename] = 0
				elif selection == -1:
					return

			driveID = SETTINGS_MODULE.getParameter("filename")	# file ID
			driveURL = "https://www.googleapis.com/drive/v2/files/{}?includeTeamDriveItems=true&supportsTeamDrives=true&alt=media".format(driveID)
			url = "http://localhost:{}/crypto_playurl".format(service.settings.serverPort)
			data = "instance={}&url={}".format(service.instanceName, driveURL)
			req = urllib.request.Request(url, data.encode("utf-8"))

			try:
				response = urllib.request.urlopen(req)
				response.close()
			except urllib.error.URLError as e:
				xbmc.log(ADDON.getAddonInfo("name") + ": " + str(e), xbmc.LOGERROR)
				return

			item = xbmcgui.ListItem(path="http://localhost:{}/play".format(service.settings.serverPort))
			# item.setProperty("StartPercent", str(position))
			# item.setProperty("startoffset", "60")

			if resumeOption:
				# item.setProperty("totaltime", "1")
				item.setProperty("totaltime", str(videoLength))
				item.setProperty("resumetime", str(resumePosition))

			xbmcplugin.setResolvedUrl(PLUGIN_HANDLE, True, item)

			if dbID:
				widget = 0 if xbmc.getInfoLabel("Container.Content") else 1
				data = "dbid={}&dbtype={}&widget={}&track={}".format(dbID, dbType, widget, 1)
			else:
				data = "dbid={}&dbtype={}&widget={}&track={}".format(0, 0, 0, 0)

			url = "http://localhost:{}/start_gplayer".format(service.settings.serverPort)
			req = urllib.request.Request(url, data.encode("utf-8"))
			response = urllib.request.urlopen(req)
			response.close()

		xbmcplugin.endOfDirectory(PLUGIN_HANDLE)
		return

				# with open(resumeDB, "wb+") as dic:
					# pickle.dump(videoData, dic)

				# del videoData

				# with open(resumeDB, "rb") as dic:
					# videoData = pickle.load(dic)

				# if player.videoWatched:
					# del videoData[filename]
				# else:
					# videoData[filename] = player.time

				# with open(resumeDB, "wb+") as dic:
					# pickle.dump(videoData, dic)

		# request = {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"field": "playcount", "operator": "greaterthan", "value": "0"}, "limits": { "start": 0 }, "properties": ["playcount"], "sort": { "order": "ascending", "method": "label" } }, "id": "libMovies"}
		# request = {"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"field": "playcount", "operator": "greaterthan", "value": "0"}, "limits": { "start": 0 }, "properties": ["playcount"], "sort": { "order": "ascending", "method": "label" } }, "id": "libMovies"}

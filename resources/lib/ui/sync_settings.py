import os
import time
import urllib

import xbmc
import xbmcgui
import xbmcaddon

import constants
from .. import sync


class SyncOptions(xbmcgui.WindowDialog):
	ACTION_MOVE_LEFT = 1
	ACTION_MOVE_RIGHT = 2
	ACTION_MOVE_UP = 3
	ACTION_MOVE_DOWN = 4
	ACTION_SELECT_ITEM = 7
	ACTION_BACKSPACE = 92
	LABELS_TO_SETTINGS = {
		"Sync path": {"type": "global", "name": "local_path"},
		"Sync mode": {"type": "drive", "name": "task_mode"},
		"Sync frequency": {"type": "drive", "name": "task_frequency"},
		"Sync at startup?": {"type": "drive", "name": "startup_sync"},
		"Does this folder contain gDrive encrypted files?": {"type": "folder", "name": "contains_encrypted"},
		"Rename videos to a Kodi friendly format?": {"type": "folder", "name": "file_renaming"},
		"Create a Kodi friendly directory structure?": {"type": "folder", "name": "folder_restructure"},
		"Sync NFOs?": {"type": "folder", "name": "sync_nfo"},
		"Sync Subtitles?": {"type": "folder", "name": "sync_subtitles"},
		"Sync Artwork?": {"type": "folder", "name": "sync_artwork"},
	}

	def __init__(self, *args, **kwargs):
		self.displayMode = kwargs.get("mode")
		self.driveID = kwargs.get("drive_id")
		self.folderID = kwargs.get("folder_id")
		self.folderName = kwargs.get("folder_name")
		self.accounts = kwargs.get("accounts")
		self.cache = sync.cache.Cache()

		self.syncMode = None
		self.syncFrequency = None

		addon = xbmcaddon.Addon()
		self.dialog = xbmcgui.Dialog()

		texturesPath = os.path.join(addon.getAddonInfo("path"), "resources", "media")
		self.radioButtonFocus = os.path.join(texturesPath, "radiobutton-focus.png")
		self.radioButtonNoFocus = os.path.join(texturesPath, "radiobutton-nofocus.png")
		self.buttonFocusTexture = os.path.join(texturesPath, "focus.png")
		self.blackTexture = os.path.join(texturesPath, "black.png")
		self.blueTexture = os.path.join(texturesPath, "blue.png")
		self.grayTexture = os.path.join(texturesPath, "gray.png")
		self.dGrayTexture = os.path.join(texturesPath, "dgray.png")
		self.createButtons()

	def setup(self, buttonAmount):
		self.font = "font13"
		self.viewportWidth = self.getWidth()
		self.viewportHeight = self.getHeight()
		self.windowWidth = int(1000 * self.viewportWidth / 1920)
		self.buttonWidth = self.windowWidth - 50
		self.buttonHeight = 40
		self.windowHeight = int((400 + self.buttonHeight * buttonAmount) * self.viewportHeight / 1080)
		self.windowBottom = int((self.viewportHeight + self.windowHeight) / 2)

		self.x = int((self.viewportWidth - self.windowWidth) / 2)
		self.y = int((self.viewportHeight - self.windowHeight) / 2)
		self.center = int((self.x + self.windowWidth / 2) - (self.buttonWidth / 2))

		background = xbmcgui.ControlImage(self.x, self.y, self.windowWidth, self.windowHeight, self.grayTexture)
		bar = xbmcgui.ControlImage(self.x, self.y, self.windowWidth, 40, self.blueTexture)
		label = xbmcgui.ControlLabel(self.x + 10, self.y + 5, 0, 0, "Sync Settings")
		self.addControls([background, bar, label])

	def onAction(self, action):
		action = action.getId()
		self.buttonID = self.getFocusId()

		if action == self.ACTION_BACKSPACE:
			self.close()
		elif action == self.ACTION_MOVE_UP:

			if self.buttonID == self.menuButtonIDs[0]:
				self.setFocus(self.buttonOK)
			elif self.buttonID in (self.buttonCloseID, self.buttonOKID):
				self.setFocusId(self.menuButtonIDs[-1])
			else:
				self.updateList("up")

		elif action == self.ACTION_MOVE_DOWN:

			if self.buttonID == self.menuButtonIDs[-1]:
				self.setFocus(self.buttonOK)
			elif self.buttonID in (self.buttonCloseID, self.buttonOKID):
				self.setFocusId(self.menuButtonIDs[0])
			else:
				self.updateList("down")

		elif action == self.ACTION_MOVE_RIGHT:

			if self.buttonID in self.menuButtonIDs or self.buttonID == self.buttonOKID:
				self.setFocus(self.buttonClose)
			elif self.buttonID == self.buttonCloseID:
				self.setFocusId(self.menuButtonIDs[0])

		elif action == self.ACTION_MOVE_LEFT:

			if self.buttonID in self.menuButtonIDs or self.buttonID == self.buttonCloseID:
				self.setFocus(self.buttonOK)
			elif self.buttonID == self.buttonOKID:
				self.setFocusId(self.menuButtonIDs[0])

	def onControl(self, control):
		self.buttonID = control.getId()

		if self.buttonID == self.buttonCloseID:
			self.close()
		elif self.buttonID == self.buttonOKID:
			self.setSettings()
		elif self.buttonID in self.pushButtonIDs:
			self.functions[control.getLabel()](control)

	def updateList(self, direction):
		currentIndex = self.menuButtonIDs.index(self.buttonID)

		if direction == "up":
			newIndex = currentIndex - 1
		elif direction == "down":
			newIndex = currentIndex + 1

			if newIndex == len(self.menuButtonIDs):
				newIndex = 0

		currentButton = self.getButton(self.menuButtonIDs[currentIndex])
		newButton = self.getButton(self.menuButtonIDs[newIndex])
		self.setFocus(newButton)

	def getLabel(self, buttonID):
		return self.getButton(buttonID).getLabel()

	def getButton(self, buttonID):
		return self.getControl(buttonID)

	def createDriveSettingsButtons(self):
		driveSettings = self.cache.getDrive(self.driveID)
		self.functions = {
			"Sync mode": self.setSyncMode,
			"Sync frequency": self.setSyncFrequency,
			"Stop syncing all folders": self.stopAllFoldersSync,
			"Stop syncing all folders and delete local files": self.stopAllFoldersSyncAndDelete,
		}
		self.syncMode = driveSettings["task_mode"]
		self.syncFrequency = driveSettings["task_frequency"]
		settings = {"Sync at startup?": driveSettings["startup_sync"]}
		self.setup(len(self.functions) + len(settings))

		for setting, value in settings.items():
			button = xbmcgui.ControlRadioButton(
				x=self.center,
				y=self.y + self.buttonSpacing,
				width=self.buttonWidth,
				height=self.buttonHeight,
				label=setting,
				font=self.font,
				noFocusOffTexture=self.radioButtonNoFocus,
				focusOffTexture=self.radioButtonNoFocus,
				focusOnTexture=self.radioButtonFocus,
				noFocusOnTexture=self.radioButtonFocus,
				focusTexture=self.buttonFocusTexture,
				noFocusTexture=self.dGrayTexture,
			)
			self.radioButtons[button] = setting
			self.addControl(button)
			button.setSelected(value)
			self.buttonSpacing += 40

		for func in self.functions:
			button = xbmcgui.ControlButton(
				x=self.center,
				y=self.y + self.buttonSpacing,
				width=self.buttonWidth,
				height=self.buttonHeight,
				label=func,
				font=self.font,
				focusTexture=self.buttonFocusTexture,
				noFocusTexture=self.dGrayTexture,
			)

			if func == "Sync mode":
				button.setLabel(label2=self.syncMode)
			elif func == "Sync frequency":
				button.setLabel(label2=self.syncFrequency)

			self.pushButtons[button] = func
			self.addControl(button)
			self.buttonSpacing += 40

	def createFolderSettingsButtons(self):
		settings = {}
		folderSettings = self.cache.getFolder(self.folderID)

		if not self.displayMode == "new" and folderSettings:
			self.functions = {
				"Stop syncing folder": self.stopFolderSync,
				"Stop syncing folder and delete local files": self.stopFolderSyncAndDelete,
			}
		else:

			if not self.cache.getSyncRootPath():
				self.functions.update({"Sync path": self.setSyncPath})

			if not self.cache.getDrive(self.driveID):
				settings.update({"Sync at startup?": False})
				self.functions.update(
					{
						"Sync mode": self.setSyncMode,
						"Sync frequency": self.setSyncFrequency,
					}
				)

		settings.update(
			{
				"Does this folder contain gDrive encrypted files?": folderSettings["contains_encrypted"] if folderSettings else False,
				"Rename videos to a Kodi friendly format?": folderSettings["file_renaming"] if  folderSettings else False,
				"Create a Kodi friendly directory structure?": folderSettings["folder_restructure"] if folderSettings else False,
				"Sync NFOs?": folderSettings["sync_nfo"] if folderSettings else False,
				"Sync Subtitles?": folderSettings["sync_subtitles"] if folderSettings else False,
				"Sync Artwork?": folderSettings["sync_artwork"] if folderSettings else False,
			}
		)
		self.setup(len(self.functions) + len(settings))

		for setting in self.functions:
			button = xbmcgui.ControlButton(
				x=self.center,
				y=self.y + self.buttonSpacing,
				width=self.buttonWidth,
				height=self.buttonHeight,
				label=setting,
				font=self.font,
				focusTexture=self.buttonFocusTexture,
				noFocusTexture=self.dGrayTexture,
			)
			self.pushButtons[button] = setting
			self.addControl(button)
			self.buttonSpacing += 40

		for setting, value in settings.items():
			button = xbmcgui.ControlRadioButton(
				x=self.center,
				y=self.y + self.buttonSpacing,
				width=self.buttonWidth,
				height=self.buttonHeight,
				label=setting,
				font=self.font,
				noFocusOffTexture=self.radioButtonNoFocus,
				focusOffTexture=self.radioButtonNoFocus,
				focusOnTexture=self.radioButtonFocus,
				noFocusOnTexture=self.radioButtonFocus,
				focusTexture=self.buttonFocusTexture,
				noFocusTexture=self.dGrayTexture,
			)
			self.radioButtons[button] = setting
			self.addControl(button)
			button.setSelected(value)
			self.buttonSpacing += 40

	def createButtons(self):
		self.buttonSpacing = 60
		self.radioButtons = {}
		self.pushButtons = {}
		self.functions = {}

		if self.displayMode in ("new", "folder"):
			self.createFolderSettingsButtons()
		else:
			self.createDriveSettingsButtons()

		self.pushButtonIDs = [button.getId() for button in self.pushButtons]
		self.radioButtonIDs = [button.getId() for button in self.radioButtons]

		if self.displayMode in ("new", "folder"):
			self.menuButtonIDs = self.pushButtonIDs + self.radioButtonIDs
		else:
			self.menuButtonIDs = self.radioButtonIDs + self.pushButtonIDs

		self.buttonOK = xbmcgui.ControlButton(
			x=self.center,
			y=self.windowBottom - 60,
			width=100,
			height=self.buttonHeight,
			label="OK",
			font=self.font,
			noFocusTexture=self.dGrayTexture,
			focusTexture=self.buttonFocusTexture,
			alignment=2 + 4,
		)
		self.buttonClose = xbmcgui.ControlButton(
			x=self.center + 120,
			y=self.windowBottom - 60,
			width=100,
			height=self.buttonHeight,
			label="Cancel",
			font=self.font,
			noFocusTexture=self.dGrayTexture,
			focusTexture=self.buttonFocusTexture,
			alignment=2 + 4,
		)
		self.addControls([self.buttonOK, self.buttonClose])
		self.buttonCloseID = self.buttonClose.getId()
		self.buttonOKID = self.buttonOK.getId()
		self.setFocusId(self.menuButtonIDs[0])

	def setSyncMode(self, button):
		modes = ["interval", "schedule"]
		selection = self.dialog.select("Sync Mode", modes)

		if selection == -1:
			return

		selection =  modes[selection]

		if selection != self.syncMode:
			[button.setLabel(label2=" ") for button, setting in self.pushButtons.items() if setting == "Sync frequency"]
			self.syncMode = selection
			button.setLabel(label2=self.syncMode)

	def setSyncFrequency(self, button):

		if not self.syncMode:
			return

		if self.syncMode == "interval":
			syncFrequency = self.dialog.numeric(0, "Enter the sync interval in minutes")
		else:
			syncFrequency = self.dialog.numeric(2, "Enter the time to sync files")

		if syncFrequency:
			button.setLabel(label2=syncFrequency)

	def stopFolderSync(self, *args):
		selection = self.dialog.yesno("gDrive", "Are you sure you want to stop syncing this folder?")

		if not selection:
			return

		self.close()
		data = f"folder_id={self.folderID}&delete=False"
		url = f"http://localhost:{constants.settings.getSettingInt('server_port', 8011)}/stop_folder_sync"
		req = urllib.request.Request(url, data.encode("utf-8"))
		response = urllib.request.urlopen(req)
		response.close()
		xbmc.executebuiltin("Container.Refresh")

	def stopAllFoldersSync(self, *args):
		selection = self.dialog.yesno("gDrive", "Are you sure you want to stop syncing all folders?")

		if not selection:
			return

		self.close()
		data = f"drive_id={self.driveID}&delete=False"
		url = f"http://localhost:{constants.settings.getSettingInt('server_port', 8011)}/stop_all_folders_sync"
		req = urllib.request.Request(url, data.encode("utf-8"))
		response = urllib.request.urlopen(req)
		response.close()
		xbmc.executebuiltin("Container.Refresh")

	def stopFolderSyncAndDelete(self, *args):
		selection = self.dialog.yesno("gDrive", "Are you sure you want to stop syncing this folder and delete its files?")

		if not selection:
			return

		self.close()
		self.dialog.notification("gDrive", "Files are now being deleted. A notication will appear when they've been deleted.")
		data = f"folder_id={self.folderID}&delete=True"
		url = f"http://localhost:{constants.settings.getSettingInt('server_port', 8011)}/stop_folder_sync"
		req = urllib.request.Request(url, data.encode("utf-8"))
		response = urllib.request.urlopen(req)
		response.close()
		xbmc.executebuiltin("Container.Refresh")

	def stopAllFoldersSyncAndDelete(self, *args):
		selection = self.dialog.yesno("gDrive", "Are you sure you want to stop syncing all folders and delete their files?")

		if not selection:
			return

		self.close()
		self.dialog.notification("gDrive", "Files are now being deleted. A notication will appear when they've been deleted.")
		data = f"drive_id={self.driveID}&delete=True"
		url = f"http://localhost:{constants.settings.getSettingInt('server_port', 8011)}/stop_all_folders_sync"
		req = urllib.request.Request(url, data.encode("utf-8"))
		response = urllib.request.urlopen(req)
		response.close()
		xbmc.executebuiltin("Container.Refresh")

	def setSyncPath(self, button):
		syncRootPath = self.dialog.browse(0, "Select the folder that your files will be stored in", "files")

		if not syncRootPath:
			return

		syncRootPath = os.path.join(syncRootPath, "gDrive")
		button.setLabel(label2=syncRootPath)

	def setSettings(self):
		globalSettings, driveSettings, folderSettings = {}, {}, {}
		settingTypes = {"global": globalSettings, "drive": driveSettings, "folder": folderSettings}

		for button, label in self.radioButtons.items():
			setting = self.LABELS_TO_SETTINGS[label]
			settingType = setting["type"]
			settingTypes[settingType].update({setting["name"]: button.isSelected()})

		for button, label in self.pushButtons.items():

			try:
				setting = self.LABELS_TO_SETTINGS[label]
				settingType = setting["type"]
				settingTypes[settingType].update({setting["name"]: button.getLabel2()})
			except KeyError:
				continue

		if folderSettings.get("contains_encrypted"):
			cryptoSalt = constants.settings.getSetting("crypto_salt")
			cryptoPassword = constants.settings.getSetting("crypto_password")

			if not cryptoSalt or not cryptoPassword:
				self.dialog.ok("gDrive", "Your encryption settings are incomplete.")
				return

		if globalSettings and not globalSettings["local_path"]:
			self.dialog.ok("gDrive", "You must assign a destination path")
			return

		if self.displayMode == "drive" or not self.cache.getDrive(self.driveID):

			if not driveSettings["task_mode"]:
				self.dialog.ok("gDrive", "You must assign a sync mode")
				return

			if driveSettings["task_frequency"] == " ":
				self.dialog.ok("gDrive", "You must assign a sync frequency")
				return

		self.close()

		if self.displayMode == "new":
			self.dialog.notification("gDrive", "Syncing files. A notification will appear when this task has completed.")

			if globalSettings:
				globalSettings.update({"operating_system": os.name})
				self.cache.addGlobalData(globalSettings)

			if driveSettings:
				alias = self.accounts[self.driveID]["alias"]
				drivePath = alias if alias else self.driveID

				driveSettings.update(
					{
						"drive_id": self.driveID,
						"local_path": drivePath,
						"last_update": time.time(),

					}
				)
				self.cache.addDrive(driveSettings)

			folderSettings.update(
				{
					"drive_id": self.driveID,
					"folder_id": self.folderID,
					"local_path": self.folderName,
				}
			)
			self.cache.addFolder(folderSettings)
			data = f"drive_id={self.driveID}&folder_id={self.folderID}&folder_name={self.folderName}"
			url = f"http://localhost:{constants.settings.getSettingInt('server_port', 8011)}/add_sync_task"
			req = urllib.request.Request(url, data.encode("utf-8"))
			response = urllib.request.urlopen(req)
			response.close()
			xbmc.executebuiltin("Container.Refresh")

		else:

			if driveSettings:
				self.cache.updateDrive(driveSettings, self.driveID)
				data = f"drive_id={self.driveID}"
				url = f"http://localhost:{constants.settings.getSettingInt('server_port', 8011)}/renew_task"
				req = urllib.request.Request(url, data.encode("utf-8"))
				response = urllib.request.urlopen(req)
				response.close()

			if folderSettings:
				self.cache.updateFolder(folderSettings, self.folderID)

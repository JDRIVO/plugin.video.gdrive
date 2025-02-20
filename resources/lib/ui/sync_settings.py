import os
import time

import xbmc
import xbmcgui
import xbmcaddon

from constants import SETTINGS
from .dialogs import Dialog
from .strm_affixer import StrmAffixer
from ..network import http_requester
from ..sync.sync_cache_manager import SyncCacheManager
from ..filesystem.fs_helpers import removeProhibitedFSchars
from ..filesystem.fs_constants import TMDB_LANGUAGES, TMDB_REGIONS


class SyncSettings(xbmcgui.WindowDialog):
	ACTION_MOVE_LEFT = 1
	ACTION_MOVE_RIGHT = 2
	ACTION_MOVE_UP = 3
	ACTION_MOVE_DOWN = 4
	ACTION_SELECT_ITEM = 7
	ACTION_PREVIOUS_MENU = 10
	ACTION_BACKSPACE = 92
	LABELS_TO_SETTINGS = {
		SETTINGS.getLocalizedString(30048): {"type": "global", "name": "local_path"},
		SETTINGS.getLocalizedString(30049): {"type": "drive", "name": "task_mode"},
		SETTINGS.getLocalizedString(30050): {"type": "drive", "name": "task_frequency"},
		SETTINGS.getLocalizedString(30051): {"type": "drive", "name": "startup_sync"},
		SETTINGS.getLocalizedString(30607): {"type": "folder", "name": "contains_encrypted"},
		SETTINGS.getLocalizedString(30608): {"type": "folder", "name": "file_renaming"},
		SETTINGS.getLocalizedString(30609): {"type": "folder", "name": "folder_renaming"},
		SETTINGS.getLocalizedString(30610): {"type": "folder", "name": "sync_nfo"},
		SETTINGS.getLocalizedString(30611): {"type": "folder", "name": "sync_subtitles"},
		SETTINGS.getLocalizedString(30612): {"type": "folder", "name": "sync_artwork"},
		SETTINGS.getLocalizedString(30613): {"type": "folder", "name": "sync_strm"},
		SETTINGS.getLocalizedString(30614): {"type": "folder", "name": "strm_prefix"},
		SETTINGS.getLocalizedString(30615): {"type": "folder", "name": "strm_suffix"},
		SETTINGS.getLocalizedString(30058): {"type": "folder", "name": "tmdb_language"},
		SETTINGS.getLocalizedString(30059): {"type": "folder", "name": "tmdb_region"},
		SETTINGS.getLocalizedString(30060): {"type": "folder", "name": "tmdb_adult"},
	}

	def __init__(self, *args, **kwargs):
		self.displayMode = kwargs.get("mode")
		self.driveID = kwargs.get("drive_id")
		self.folderID = kwargs.get("folder_id")
		self.folderName = kwargs.get("folder_name")
		self.foldersToSync = kwargs.get("folders")
		self.accounts = kwargs.get("accounts")
		self.settings = SETTINGS
		self.cache = SyncCacheManager()
		self.dialog = Dialog()
		self.driveSettings = self.cache.getDrive(self.driveID)
		self.syncMode = self.driveSettings["task_mode"] if self.driveSettings else None
		self.syncFrequency = self.driveSettings["task_frequency"] if self.driveSettings else None
		self.folders = False
		self.font = "font13"
		self.buttonSpacing = 60
		self._initializePaths()
		self._createButtons()

	def onAction(self, action):
		action = action.getId()
		self.buttonID = self.getFocusId()

		if action in (self.ACTION_PREVIOUS_MENU, self.ACTION_BACKSPACE):
			self.close()
		elif action == self.ACTION_MOVE_UP:

			if self.buttonID == self.menuButtonIDs[0]:
				self.setFocus(self.buttonOK)
			elif self.buttonID in (self.buttonCloseID, self.buttonOKid):
				self.setFocusId(self.menuButtonIDs[-1])
			elif self.buttonID in self.menuButtonIDs:
				self._updateList("up")

		elif action == self.ACTION_MOVE_DOWN:

			if self.buttonID == self.menuButtonIDs[-1]:
				self.setFocus(self.buttonOK)
			elif self.buttonID in (self.buttonCloseID, self.buttonOKid):
				self.setFocusId(self.menuButtonIDs[0])
			elif self.buttonID in self.menuButtonIDs:
				self._updateList("down")

		elif action == self.ACTION_MOVE_RIGHT:

			if self.folders:

				if self.buttonID in self.menuButtonIDs or self.buttonID == self.buttonOKid:
					self.setFocus(self.buttonClose)
				elif self.buttonID in self.buttonSwitchesIDs:
					self.setFocusId(self.menuButtonIDs[0])
				elif self.buttonID == self.buttonCloseID:
					self.setFocusId(self.menuButtonIDs[0])

			else:

				if self.buttonID in self.menuButtonIDs or self.buttonID == self.buttonOKid:
					self.setFocus(self.buttonClose)
				elif self.buttonID == self.buttonCloseID:
					self.setFocusId(self.menuButtonIDs[0])

		elif action == self.ACTION_MOVE_LEFT:

			if self.folders:

				if self.buttonID in self.menuButtonIDs:
					self.setFocusId(self.buttonSwitchesIDs[0])
				elif self.buttonID in self.buttonSwitchesIDs:
					self.setFocus(self.buttonOK)
				elif self.buttonID == self.buttonCloseID:
					self.setFocus(self.buttonOK)
				elif self.buttonID == self.buttonOKid:
					self.setFocusId(self.menuButtonIDs[0])

			else:

				if self.buttonID in self.menuButtonIDs or self.buttonID == self.buttonCloseID:
					self.setFocus(self.buttonOK)
				elif self.buttonID == self.buttonOKid:
					self.setFocusId(self.menuButtonIDs[0])

	def onControl(self, control):
		self.buttonID = control.getId()

		if self.buttonID in (self.backgroundID, self.buttonCloseID):
			self.close()
		elif self.buttonID == self.buttonOKid:
			self._setSettings()
		elif self.buttonID in self.pushButtonIDs:
			self.functions[control.getLabel()](control)
		elif self.buttonID in self.buttonSwitchesIDs:

			if self.buttonID == self.buttonSwitchesIDs[0]:
				[button.setVisible(False) for button in self.TMDBButtons]
				[button.setVisible(True) for button in self.generalSettingsButtons]
				self.menuButtonIDs = self.generalSettingsButtonIDs
			else:
				[button.setVisible(False) for button in self.generalSettingsButtons]
				[button.setVisible(True) for button in self.TMDBButtons]
				self.menuButtonIDs = self.TMDBButtonIDs

	def _addBackground(self):
		backgroundInvis = xbmcgui.ControlButton(0, 0, self.viewportWidth, self.viewportHeight, "", focusTexture="", noFocusTexture="")
		background = xbmcgui.ControlButton(self.x, self.y, self.windowWidth, self.windowHeight, "", focusTexture=self.grayTexture, noFocusTexture=self.grayTexture)
		bar = xbmcgui.ControlButton(
			self.x,
			self.y,
			self.windowWidth,
			40,
			f"[B]{self.settings.getLocalizedString(30012)}{': ' + self.folderName if self.folderName else ''}[/B]",
			focusTexture=self.blueTexture,
			noFocusTexture=self.blueTexture,
			shadowColor="0xFF000000",
			textOffsetX=20
		)
		self.addControls([backgroundInvis, background, bar])
		self.backgroundID = backgroundInvis.getId()

	def _addControlButton(self, label, x, folderSettings=None):
		button = xbmcgui.ControlButton(
			x=x,
			y=self.y + self.buttonSpacing,
			width=self.buttonWidth,
			height=self.buttonHeight,
			label=label,
			font=self.font,
			focusTexture=self.focusTexture,
			noFocusTexture=self.dGrayTexture,
		)

		if label == self.settings.getLocalizedString(30614):
			button.setLabel(label2=folderSettings["strm_prefix"] if folderSettings else self.settings.getSetting("strm_prefix"))
		elif label == self.settings.getLocalizedString(30615):
			button.setLabel(label2=folderSettings["strm_suffix"] if folderSettings else self.settings.getSetting("strm_suffix"))
		elif label == self.settings.getLocalizedString(30049):
			button.setLabel(label2=self.syncMode)
		elif label == self.settings.getLocalizedString(30050):
			button.setLabel(label2=self.syncFrequency)

		self.addControl(button)
		self.pushButtons[button] = label
		self.buttonSpacing += 40

	def _addRadioButton(self, label, isEnabled, x):
		button = xbmcgui.ControlRadioButton(
			x=x,
			y=self.y + self.buttonSpacing,
			width=self.buttonWidth,
			height=self.buttonHeight,
			label=label,
			font=self.font,
			noFocusOffTexture=self.focusOffTexture,
			focusOffTexture=self.focusOffTexture,
			focusOnTexture=self.focusOnTexture,
			noFocusOnTexture=self.focusOnTexture,
			focusTexture=self.focusTexture,
			noFocusTexture=self.dGrayTexture,
		)
		self.addControl(button)
		self.radioButtons[button] = label
		button.setSelected(isEnabled)
		self.buttonSpacing += 40

	def _calculateViewport(self):
		self.viewportWidth = self.getWidth()
		self.viewportHeight = self.getHeight()
		self.windowWidth = int(1000 * self.viewportWidth / 1920)

		if self.folders:
			self.buttonWidth = self.windowWidth - 200
		else:
			self.buttonWidth = self.windowWidth - 50

		self.buttonHeight = 40
		self.windowHeight = int(self.buttonHeight * self.buttonAmount + self.buttonSpacing + 90)
		self.windowBottom = int((self.viewportHeight + self.windowHeight) / 2)
		self.x = int((self.viewportWidth - self.windowWidth) / 2)
		self.y = int((self.viewportHeight - self.windowHeight) / 2)
		self.center = int((self.x + self.windowWidth / 2) - (self.buttonWidth / 2))

	def _createButtons(self):
		self.radioButtons, self.pushButtons = {}, {}
		self.buttonSwitchesIDs = []

		if self.displayMode in ("new", "folder"):
			self.folders = True
			self._createFolderSettingsButtons()
			self._createFolderSettingsTMDBButtons()
		else:
			self._createDriveSettingsButtons()

		self.pushButtonIDs = [button.getId() for button in self.pushButtons]
		self.buttonOK = xbmcgui.ControlButton(
			x=self.center + 80 if self.folders else self.center,
			y=self.windowBottom - 60,
			width=100,
			height=self.buttonHeight,
			label=self.settings.getLocalizedString(30066),
			font=self.font,
			noFocusTexture=self.dGrayTexture,
			focusTexture=self.focusTexture,
			alignment=2 + 4,
		)
		self.buttonClose = xbmcgui.ControlButton(
			x=self.center + 200 if self.folders else self.center + 120,
			y=self.windowBottom - 60,
			width=100,
			height=self.buttonHeight,
			label=self.settings.getLocalizedString(30067),
			font=self.font,
			noFocusTexture=self.dGrayTexture,
			focusTexture=self.focusTexture,
			alignment=2 + 4,
		)
		self.addControls([self.buttonOK, self.buttonClose])
		self.buttonCloseID = self.buttonClose.getId()
		self.buttonOKid = self.buttonOK.getId()
		self.setFocusId(self.menuButtonIDs[0])

	def _createDriveSettingsButtons(self):
		self.functions = {
			self.settings.getLocalizedString(30049): self._setSyncMode,
			self.settings.getLocalizedString(30050): self._setSyncFrequency,
			self.settings.getLocalizedString(30061): self._stopSyncingFolders,
			self.settings.getLocalizedString(30062): self._stopSyncingFoldersAndDelete,
		}
		radioButtons = {self.settings.getLocalizedString(30051): self.driveSettings["startup_sync"]}
		self.buttonAmount = len(self.functions) + len(radioButtons)
		self._calculateViewport()
		self._addBackground()

		for setting, isEnabled in radioButtons.items():
			self._addRadioButton(setting, isEnabled, self.center)

		for setting in self.functions:
			self._addControlButton(setting, self.center)

		self.generalSettingsButtons = list(self.radioButtons.keys()) + list(self.pushButtons.keys())
		self.generalSettingsButtonIDs = [button.getId() for button in self.generalSettingsButtons]
		self.menuButtonIDs = self.generalSettingsButtonIDs

	def _createFolderSettingsButtons(self):
		folderSettings = self.cache.getFolder({"folder_id": self.folderID})
		self.functions, radioButtons = {}, {}

		if not self.displayMode == "new" and folderSettings:
			self.functions.update(
				{
					self.settings.getLocalizedString(30063): self._stopSyncingFolder,
					self.settings.getLocalizedString(30064): self._stopSyncingFolderAndDelete,
				}
			)
		else:

			if not self.cache.getSyncRootPath():
				self.functions.update({self.settings.getLocalizedString(30048): self._setSyncPath})

			if not self.cache.getDrive(self.driveID):
				radioButtons.update({self.settings.getLocalizedString(30051): False})
				self.functions.update(
					{
						self.settings.getLocalizedString(30049): self._setSyncMode,
						self.settings.getLocalizedString(30050): self._setSyncFrequency,
					}
				)

		radioButtons.update(
			{
				self.settings.getLocalizedString(30607): folderSettings["contains_encrypted"] if folderSettings else self.settings.getSetting("contains_encrypted"),
				self.settings.getLocalizedString(30608): folderSettings["file_renaming"] if folderSettings else self.settings.getSetting("file_renaming"),
				self.settings.getLocalizedString(30609): folderSettings["folder_renaming"] if folderSettings else self.settings.getSetting("folder_renaming"),
				self.settings.getLocalizedString(30610): folderSettings["sync_nfo"] if folderSettings else self.settings.getSetting("sync_nfo"),
				self.settings.getLocalizedString(30611): folderSettings["sync_subtitles"] if folderSettings else self.settings.getSetting("sync_subtitles"),
				self.settings.getLocalizedString(30612): folderSettings["sync_artwork"] if folderSettings else self.settings.getSetting("sync_artwork"),
				self.settings.getLocalizedString(30613): folderSettings["sync_strm"] if folderSettings else self.settings.getSetting("sync_strm"),
			}
		)
		self.functions.update(
			{
				self.settings.getLocalizedString(30614): self._setPrefix,
				self.settings.getLocalizedString(30615): self._setSuffix,
			}
		)
		self.buttonAmount = len(self.functions) + len(radioButtons)
		self._calculateViewport()
		self._addBackground()

		for setting in self.functions:
			self._addControlButton(setting, self.center + 80, folderSettings)

		for setting, isEnabled in radioButtons.items():
			self._addRadioButton(setting, isEnabled, self.center + 80)

		self.generalSettingsButtons = list(self.pushButtons.keys()) + list(self.radioButtons.keys())
		self.generalSettingsButtonIDs = [button.getId() for button in self.generalSettingsButtons]
		self.menuButtonIDs = self.generalSettingsButtonIDs

	def _createFolderSettingsTMDBButtons(self):
		functions = {
			self.settings.getLocalizedString(30058): self._setSearchLanguage,
			self.settings.getLocalizedString(30059): self._setCountry,
			self.settings.getLocalizedString(30060): self._setAdultContent,
		}
		self.functions.update(functions)
		buttonGeneral = xbmcgui.ControlButton(
			x=self.center - 80,
			y=self.y + 60,
			width=140,
			height=self.buttonHeight,
			label=self.settings.getLocalizedString(30065),
			font=self.font,
			focusTexture=self.focusTexture,
			noFocusTexture=self.dGrayTexture,
			alignment=2 + 4,
		)
		self.addControl(buttonGeneral)
		self.buttonSwitchesIDs.append(buttonGeneral.getId())
		buttonTMDB = xbmcgui.ControlButton(
			x=self.center - 80,
			y=self.y + 100,
			width=140,
			height=self.buttonHeight,
			label="TMDB",
			font=self.font,
			focusTexture=self.focusTexture,
			noFocusTexture=self.dGrayTexture,
			alignment=2 + 4,
		)
		self.addControl(buttonTMDB)
		self.buttonSwitchesIDs.append(buttonTMDB.getId())
		buttonGeneral.controlUp(buttonTMDB)
		buttonGeneral.controlDown(buttonTMDB)
		buttonTMDB.controlUp(buttonGeneral)
		buttonTMDB.controlDown(buttonGeneral)
		buttonSpacing = 60
		self.TMDBButtons, self.TMDBButtonIDs = [], []
		folderSettings = self.cache.getFolder({"folder_id": self.folderID})

		if folderSettings:
			values = [
				folderSettings["tmdb_language"],
				folderSettings["tmdb_region"],
				folderSettings["tmdb_adult"],
			]
		else:
			values = [
				self.settings.getSetting("tmdb_language") or "",
				self.settings.getSetting("tmdb_region") or "",
				"true" if self.settings.getSetting("tmdb_adult") else "false",
			]

		for func, value in zip(functions, values):
			button = xbmcgui.ControlButton(
				x=self.center + 80,
				y=self.y + buttonSpacing,
				width=self.buttonWidth,
				height=self.buttonHeight,
				label=func,
				font=self.font,
				focusTexture=self.focusTexture,
				noFocusTexture=self.dGrayTexture,
			)
			button.setVisible(False)
			button.setLabel(label2=value)
			self.pushButtons[button] = func
			self.addControl(button)
			buttonSpacing += 40
			self.TMDBButtonIDs.append(button.getId())
			self.TMDBButtons.append(button)

	def _getButton(self, buttonID):
		return self.getControl(buttonID)

	def _initializePaths(self):
		mediaPath = os.path.join(xbmcaddon.Addon().getAddonInfo("path"), "resources", "media")
		self.blueTexture = os.path.join(mediaPath, "blue.png")
		self.grayTexture = os.path.join(mediaPath, "gray.png")
		self.dGrayTexture = os.path.join(mediaPath, "dgray.png")
		self.focusTexture = os.path.join(mediaPath, "focus.png")
		self.focusOnTexture = os.path.join(mediaPath, "radiobutton-focus.png")
		self.focusOffTexture = os.path.join(mediaPath, "radiobutton-nofocus.png")

	def _setAdultContent(self, button):
		options = ["true", "false"]
		selection = self.dialog.select(self.settings.getLocalizedString(30616), options)

		if selection == -1:
			return

		button.setLabel(label2=options[selection])

	def _setAffix(self, button, affix):
		folderSettings = self.cache.getFolder({"folder_id": self.folderID})
		excluded = ["duration", "extension", "resolution"]

		if button.getLabel2():
			included = [a for a in button.getLabel2().split(", ") if a != " "]
		else:
			included = [a for a in folderSettings[f"strm_{affix.lower()}"].split(", ") if a] if folderSettings else [a for a in self.settings.getSetting(f"strm_{affix.lower()}").split(", ") if a]

		for prefix in included:
			excluded.remove(prefix)

		strmAffixer = StrmAffixer(included=included, excluded=excluded, title=f"STRM {affix}")
		strmAffixer.doModal()
		closed = strmAffixer.closed
		del strmAffixer

		if closed:
			return

		newLabel = ", ".join(included)

		if newLabel:
			button.setLabel(label2=newLabel)
		else:
			button.setLabel(label2=" ")

	def _setCountry(self, button):
		selection = self.dialog.select(self.settings.getLocalizedString(30615), TMDB_REGIONS)

		if selection == -1:
			return

		button.setLabel(label2=TMDB_REGIONS[selection])

	def _setPrefix(self, button):
		self._setAffix(button, "Prefix")

	def _setSearchLanguage(self, button):
		selection = self.dialog.select(self.settings.getLocalizedString(30614), TMDB_LANGUAGES)

		if selection == -1:
			return

		button.setLabel(label2=TMDB_LANGUAGES[selection])

	def _setSettings(self):
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
				settingTypes[settingType].update({setting["name"]: button if (button := button.getLabel2()) != " " else ""})
			except KeyError:
				continue

		if folderSettings.get("contains_encrypted"):
			cryptoSalt = self.settings.getSetting("crypto_salt")
			cryptoPassword = self.settings.getSetting("crypto_password")

			if not cryptoSalt or not cryptoPassword:
				self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30078))
				return

		if globalSettings and not globalSettings["local_path"]:
			self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30079))
			return

		if self.displayMode == "drive" or not self.cache.getDrive(self.driveID):

			if not driveSettings["task_mode"]:
				self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30080))
				return

			if not driveSettings["task_frequency"] and driveSettings["task_mode"] != "manual":
				self.dialog.ok(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30081))
				return

		self.close()

		if self.displayMode != "new":

			if driveSettings:
				self.cache.updateDrive(driveSettings, self.driveID)
				data = {"drive_id": self.driveID}
				url = f"http://localhost:{self.settings.getSettingInt('server_port', 8011)}/reset_task"
				http_requester.request(url, data)

			if folderSettings:
				self.cache.updateFolder(folderSettings, self.folderID)

		else:
			self.dialog.notification(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30082))

			if globalSettings:
				globalSettings.update({"operating_system": os.name})
				self.cache.addGlobalData(globalSettings)
				self.settings.setSetting("sync_root", globalSettings["local_path"])

			if driveSettings:
				alias = self.accounts[self.driveID]["alias"]
				drivePath = alias or self.driveID
				driveSettings.update(
					{
						"drive_id": self.driveID,
						"local_path": drivePath,
						"last_update": time.time(),

					}
				)
				self.cache.addDrive(driveSettings)

			syncTaskData = [self.driveID]

			for folder in self.foldersToSync:
				folderID = folder["id"]
				folderExists = self.cache.getFolder({"folder_id": folderID})

				if folderExists:
					continue

				syncTaskData.append(folder)
				folderName = removeProhibitedFSchars(folder["name"])
				dirPath = self.cache.getUniqueFolderPath(self.driveID, folderName)
				folder["name"] = folderName
				folder["path"] = dirPath
				folderSettings.update(
					{
						"drive_id": self.driveID,
						"folder_id": folderID,
						"local_path": dirPath,
						"remote_name": folderName,
					}
				)
				self.cache.addFolder(folderSettings)

			url = f"http://localhost:{self.settings.getSettingInt('server_port', 8011)}/add_sync_task"
			xbmc.executebuiltin("Container.Refresh")
			http_requester.request(url, syncTaskData)

	def _setSuffix(self, button):
		self._setAffix(button, "Suffix")

	def _setSyncFrequency(self, button):

		if not self.syncMode or self.syncMode == self.settings.getLocalizedString(30087):
			return

		if self.syncMode == self.settings.getLocalizedString(30068):
			syncFrequency = self.dialog.numeric(0, self.settings.getLocalizedString(30070))
		else:
			syncFrequency = self.dialog.numeric(2, self.settings.getLocalizedString(30071))

		if syncFrequency:
			button.setLabel(label2=syncFrequency)

	def _setSyncMode(self, button):
		modes = [self.settings.getLocalizedString(30068), self.settings.getLocalizedString(30069), self.settings.getLocalizedString(30087)]
		selection = self.dialog.select(self.settings.getLocalizedString(30049), modes)

		if selection == -1:
			return

		selection = modes[selection]

		if selection != self.syncMode:
			[button.setLabel(label2=" ") for button, setting in self.pushButtons.items() if setting == self.settings.getLocalizedString(30050)]
			self.syncMode = selection
			button.setLabel(label2=self.syncMode)

	def _setSyncPath(self, button):
		syncRootPath = self.dialog.browse(3, self.settings.getLocalizedString(30077), "local")

		if not syncRootPath:
			return

		syncRootPath = os.path.join(syncRootPath, self.settings.getLocalizedString(30000))
		button.setLabel(label2=syncRootPath)

	def _stopSyncingFolder(self, *args):
		selection = self.dialog.yesno(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30072))

		if not selection:
			return

		self.close()
		data = {"drive_id": self.driveID, "folder_id": self.folderID, "delete": False}
		url = f"http://localhost:{self.settings.getSettingInt('server_port', 8011)}/stop_syncing_folder"
		http_requester.request(url, data)

	def _stopSyncingFolderAndDelete(self, *args):
		selection = self.dialog.yesno(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30074))

		if not selection:
			return

		self.close()
		self.dialog.notification(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30075))
		data = {"drive_id": self.driveID, "folder_id": self.folderID, "delete": True}
		url = f"http://localhost:{self.settings.getSettingInt('server_port', 8011)}/stop_syncing_folder"
		http_requester.request(url, data)

	def _stopSyncingFolders(self, *args):
		selection = self.dialog.yesno(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30073))

		if not selection:
			return

		self.close()
		data = {"drive_id": self.driveID, "delete": False}
		url = f"http://localhost:{self.settings.getSettingInt('server_port', 8011)}/stop_syncing_folders"
		http_requester.request(url, data)

	def _stopSyncingFoldersAndDelete(self, *args):
		selection = self.dialog.yesno(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30076))

		if not selection:
			return

		self.close()
		self.dialog.notification(self.settings.getLocalizedString(30000), self.settings.getLocalizedString(30075))
		data = {"drive_id": self.driveID, "delete": True}
		url = f"http://localhost:{self.settings.getSettingInt('server_port', 8011)}/stop_syncing_folders"
		http_requester.request(url, data)

	def _updateList(self, direction):
		currentIndex = self.menuButtonIDs.index(self.buttonID)

		if direction == "up":
			newIndex = currentIndex - 1
		elif direction == "down":
			newIndex = (currentIndex + 1) % len(self.menuButtonIDs)

		newButton = self._getButton(self.menuButtonIDs[newIndex])
		self.setFocus(newButton)

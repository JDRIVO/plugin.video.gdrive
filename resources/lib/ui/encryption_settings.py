import os
import re

import xbmcgui
import xbmcaddon

from constants import SETTINGS
from .dialogs import Dialog
from ..encryption import encryption_profiles
from ..encryption.profile_manager import ProfileManager
from ..encryption.encryption_types import EncryptionType


class EncryptionSettings(xbmcgui.WindowDialog):
	ACTION_MOVE_LEFT = 1
	ACTION_MOVE_RIGHT = 2
	ACTION_MOVE_UP = 3
	ACTION_MOVE_DOWN = 4
	ACTION_SELECT_ITEM = 7
	ACTION_PREVIOUS_MENU = 10
	ACTION_BACKSPACE = 92
	PUSH_LABELS = {
		"profile_name": SETTINGS.getLocalizedString(30107),
		"encryption_type": SETTINGS.getLocalizedString(30108),
		"password": SETTINGS.getLocalizedString(30109),
		"salt": SETTINGS.getLocalizedString(30110),
		"filename_encryption": SETTINGS.getLocalizedString(30111),
		"filename_encoding": SETTINGS.getLocalizedString(30112),
		"suffix": SETTINGS.getLocalizedString(30113),
	}
	RADIO_LABELS = {
		"encrypt_data": SETTINGS.getLocalizedString(30114),
		"encrypt_dir_names":SETTINGS.getLocalizedString(30115),
	}

	def __init__(self, mode=None, profile=None):
		self.mode = mode
		self.profile = profile or encryption_profiles.GDriveEncryptionProfile()
		self.profileID = profile.id if profile else None
		self.profileManager = ProfileManager()
		self.settings = SETTINGS
		self.dialog = Dialog()
		self.modified = False
		self.font = "font13"
		self._initializePaths()
		self._createButtons()

	def onAction(self, action):
		action = action.getId()
		self.buttonID = self.getFocusId()

		if action in (self.ACTION_PREVIOUS_MENU, self.ACTION_BACKSPACE):
			self.close()
		elif action == self.ACTION_MOVE_UP:

			if self.buttonID == self.visibleButtonIDs[0]:
				self.setFocus(self.buttonOK)
			elif self.buttonID in (self.buttonCloseID, self.buttonOKid):
				self.setFocusId(self.visibleButtonIDs[-1])
			elif self.buttonID in self.visibleButtonIDs:
				self._updateList("up")

		elif action == self.ACTION_MOVE_DOWN:

			if self.buttonID == self.visibleButtonIDs[-1]:
				self.setFocus(self.buttonOK)
			elif self.buttonID in (self.buttonCloseID, self.buttonOKid):
				self.setFocusId(self.visibleButtonIDs[0])
			elif self.buttonID in self.visibleButtonIDs:
				self._updateList("down")

		elif action == self.ACTION_MOVE_RIGHT:

			if self.buttonID in self.visibleButtonIDs or self.buttonID == self.buttonOKid:
				self.setFocus(self.buttonClose)
			elif self.buttonID == self.buttonCloseID:
				self.setFocusId(self.visibleButtonIDs[0])

		elif action == self.ACTION_MOVE_LEFT:

			if self.buttonID in self.visibleButtonIDs or self.buttonID == self.buttonCloseID:
				self.setFocus(self.buttonOK)
			elif self.buttonID == self.buttonOKid:
				self.setFocusId(self.visibleButtonIDs[0])

	def onControl(self, control):
		self.buttonID = control.getId()

		if self.buttonID in (self.backgroundID, self.buttonCloseID):
			self.close()
		elif self.buttonID == self.buttonOKid:
			saved = self._saveProfile()

			if saved:
				self.close()
				self._displayNotification()

		elif self.buttonID in self.buttonHandlers:
			self.buttonHandlers[self.buttonID](control)
		elif self.buttonID in self.radioButtons:
			self._setRadioSetting(control, self.radioButtons[self.buttonID])

	def _addBackground(self):
		backgroundFade = xbmcgui.ControlImage(0, 0, self.viewportWidth, self.viewportHeight, self.blackTexture,	 colorDiffuse="CCFFFFFF")
		backgroundInvis = xbmcgui.ControlButton(0, 0, self.viewportWidth, self.viewportHeight, "", focusTexture="", noFocusTexture="")
		background = xbmcgui.ControlButton(self.x, self.y, self.windowWidth, self.windowHeight, "", focusTexture=self.grayTexture, noFocusTexture=self.grayTexture)
		bar = xbmcgui.ControlButton(
			self.x,
			self.y,
			self.windowWidth,
			40,
			f"[B]{self.settings.getLocalizedString(30123)}[/B]",
			focusTexture=self.blueTexture,
			noFocusTexture=self.blueTexture,
			shadowColor="0xFF000000",
			textOffsetX=20
		)
		self.addControls([backgroundFade, backgroundInvis, background, bar])
		self.backgroundID = backgroundInvis.getId()

	def _addControlButton(self, setting):
		button = xbmcgui.ControlButton(
			x=0,
			y=0,
			width=self.buttonWidth,
			height=self.buttonHeight,
			label=self.PUSH_LABELS[setting],
			font=self.font,
			focusTexture=self.focusTexture,
			noFocusTexture=self.dGrayTexture,
		)
		self.buttons[setting] = button
		return button

	def _addRadioButton(self, setting):
		button = xbmcgui.ControlRadioButton(
			x=0,
			y=0,
			width=self.buttonWidth,
			height=self.buttonHeight,
			label=self.RADIO_LABELS[setting],
			font=self.font,
			noFocusOffTexture=self.focusOffTexture,
			focusOffTexture=self.focusOffTexture,
			focusOnTexture=self.focusOnTexture,
			noFocusOnTexture=self.focusOnTexture,
			focusTexture=self.focusTexture,
			noFocusTexture=self.dGrayTexture,
		)
		self.buttons[setting] = button
		return button

	def _calculateDimensions(self):
		self.viewportWidth = self.getWidth()
		self.viewportHeight = self.getHeight()
		self.windowWidth = int(1000 * self.viewportWidth / 1920)
		self.buttonWidth = self.windowWidth - 50
		self.buttonHeight = 40
		self.buttonSpacing = 60
		self.windowHeight = int(self.buttonHeight * self.buttonAmount + self.buttonSpacing + 50)
		self.windowBottom = int((self.viewportHeight + self.windowHeight) / 2)
		self.x = int((self.viewportWidth - self.windowWidth) / 2)
		self.y = int((self.viewportHeight - self.windowHeight) / 2)
		self.center = int(self.x + (self.windowWidth - self.buttonWidth) / 2)

	def _createButtons(self):
		self.radioButtons, self.buttons = {}, {}
		self.buttonAmount = len(self.PUSH_LABELS) + len(self.RADIO_LABELS)
		self._calculateDimensions()
		self._addBackground()
		pushButtons = [self._addControlButton(setting) for setting in self.PUSH_LABELS]
		radioButtons = {self._addRadioButton(setting): setting for setting in self.RADIO_LABELS}
		self.buttonOK = xbmcgui.ControlButton(
			x=self.center,
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
			x=self.center + 120,
			y=self.windowBottom - 60,
			width=100,
			height=self.buttonHeight,
			label=self.settings.getLocalizedString(30067),
			font=self.font,
			noFocusTexture=self.dGrayTexture,
			focusTexture=self.focusTexture,
			alignment=2 + 4,
		)
		self.addControls(pushButtons + list(radioButtons.keys()) + [self.buttonOK, self.buttonClose])
		self.buttonCloseID = self.buttonClose.getId()
		self.buttonOKid = self.buttonOK.getId()
		self.radioButtons = {button.getId(): setting for button, setting in radioButtons.items()}
		self.buttonHandlers = {
			self.buttons["profile_name"].getId(): self._setProfileName,
			self.buttons["encryption_type"].getId(): self._setEncryptionType,
			self.buttons["password"].getId(): self._setPassword,
			self.buttons["salt"].getId(): self._setSalt,
			self.buttons["filename_encryption"].getId(): self._setFilenameEncryption,
			self.buttons["filename_encoding"].getId(): self._setFilenameEncoding,
			self.buttons["suffix"].getId(): self._setSuffix,
		}
		self._setLabels()
		self._resetButtonsVisibility()
		self.setFocusId(self.visibleButtonIDs[0])

	def _displayNotification(self):

		if self.mode == "add":
			self.dialog.ok(SETTINGS.getLocalizedString(30000), SETTINGS.getLocalizedString(30124))
		else:
			self.dialog.ok(SETTINGS.getLocalizedString(30000), SETTINGS.getLocalizedString(30125))

	def _initializePaths(self):
		mediaPath = os.path.join(xbmcaddon.Addon().getAddonInfo("path"), "resources", "media")
		self.blackTexture = os.path.join(mediaPath, "black.png")
		self.blueTexture = os.path.join(mediaPath, "blue.png")
		self.grayTexture = os.path.join(mediaPath, "gray.png")
		self.dGrayTexture = os.path.join(mediaPath, "dgray.png")
		self.focusTexture = os.path.join(mediaPath, "focus.png")
		self.focusOnTexture = os.path.join(mediaPath, "radiobutton-focus.png")
		self.focusOffTexture = os.path.join(mediaPath, "radiobutton-nofocus.png")

	def _resetButtonsVisibility(self):
		settingsVisible = ["profile_name", "encryption_type", "password", "salt"]

		if self.profile.type == EncryptionType.GDRIVE:
			settingsInvisible = ["filename_encryption", "filename_encoding", "suffix", "encrypt_data", "encrypt_dir_names"]
		else:
			settingsVisible += ["filename_encryption", "encrypt_data"]

			if self.profile.filenameEncryption == "off":
				settingsVisible += ["suffix"]
				settingsInvisible = ["filename_encoding", "encrypt_dir_names"]
			else:
				settingsVisible += ["filename_encoding", "encrypt_dir_names"]
				settingsInvisible = ["suffix"]

		self._setButtonsVisibility(settingsVisible, True)
		self._setButtonsVisibility(settingsInvisible, False)
		self._updateButtonPositions()

	def _saveProfile(self):

		if not self.profile.name:
			self.dialog.ok(SETTINGS.getLocalizedString(30000), SETTINGS.getLocalizedString(30126))
			return
		elif not self.profile.password:
			self.dialog.ok(SETTINGS.getLocalizedString(30000), SETTINGS.getLocalizedString(30127))
			return
		elif self.profile.type == EncryptionType.GDRIVE and not self.profile.salt:
			self.dialog.ok(SETTINGS.getLocalizedString(30000), SETTINGS.getLocalizedString(30128))
			return

		if self.mode == "add":
			self.profileManager.addProfile(self.profile)
		else:
			self.profileManager.updateProfile(self.profileID, self.profile)
			self.modified = True

		return True

	def _setButtonsVisibility(self, settings, visible):
		[self.buttons[setting].setVisible(visible) for setting in settings]

	def _setEncryptionType(self, button):
		encryptionTypes = [EncryptionType.GDRIVE.value, EncryptionType.RCLONE.value]
		selection = self.dialog.select(SETTINGS.getLocalizedString(30108), encryptionTypes)

		if selection == -1:
			return

		type = encryptionTypes[selection]
		button.setLabel(label2=type)
		type = EncryptionType[type.upper()]
		self._setProfile(type=type)
		self._setLabels()
		self._resetButtonsVisibility()

	def _setFilenameEncoding(self, button):
		encodingTypes = ["base32", "base64", "base32768"]
		selection = self.dialog.select(SETTINGS.getLocalizedString(30112), encodingTypes)

		if selection == -1:
			return

		type = encodingTypes[selection]
		button.setLabel(label2=type)
		self.profile.filenameEncoding = type

	def _setFilenameEncryption(self, button):
		encryptionTypes = ["standard", "obfuscate", "off"]
		selection = self.dialog.select(SETTINGS.getLocalizedString(30111), encryptionTypes)

		if selection == -1:
			return

		type = encryptionTypes[selection]
		button.setLabel(label2=type)
		self.profile.filenameEncryption = type
		settingsVisible = ["profile_name", "encryption_type", "password", "salt", "filename_encryption", "encrypt_data"]

		if type == "off":
			settingsVisible += ["suffix"]
			settingsInvisible = ["filename_encoding", "encrypt_dir_names"]
		else:
			settingsVisible += ["filename_encoding", "encrypt_dir_names"]
			settingsInvisible = ["suffix"]
			self.buttons["filename_encoding"].setLabel(label2=self.profile.filenameEncoding)

		self._setButtonsVisibility(settingsInvisible, False)
		self._setButtonsVisibility(settingsVisible, True)
		self._updateButtonPositions()

	def _setLabels(self):
		settings = {
			"profile_name": self.profile.name,
			"encryption_type": self.profile.type.value,
			"password": self.profile.password or " ",
			"salt": self.profile.salt or " ",
		}

		if self.profile.type == EncryptionType.RCLONE:
			settings.update(
				{
					"filename_encryption": self.profile.filenameEncryption,
					"filename_encoding": self.profile.filenameEncoding,
					"suffix": self.profile.suffix or " ",
					"encrypt_data": self.profile.encryptData,
					"encrypt_dir_names": self.profile.encryptDirNames,
				}
			)

		[self.buttons[label].setLabel(label2=settings.get(label)) for label in self.PUSH_LABELS]
		[self.buttons[label].setSelected(settings.get(label) or 0) for label in self.RADIO_LABELS]

	def _setPassword(self, button):

		if password := self.dialog.input(SETTINGS.getLocalizedString(30109)):
			button.setLabel(label2=password)
			self.profile.password = password

	def _setProfile(self, profile=None, type=None):

		if profile:
			self.profile = profile
		elif type:
			name = self.profile.name

			if type == EncryptionType.GDRIVE:
				self.profile = encryption_profiles.GDriveEncryptionProfile()
			else:
				self.profile = encryption_profiles.RcloneEncryptionProfile()

			self.profile.name = name

		else:
			self.profile = encryption_profiles.GDriveEncryptionProfile()

	def _setProfileName(self, button):
		name = self.dialog.input(SETTINGS.getLocalizedString(30107))

		if not name:
			return

		button.setLabel(label2=name)
		self.profile.name = name

	def _setRadioSetting(self, button, setting):
		isSelected = button.isSelected()

		if setting == "encrypt_data":
			self.profile.encryptData = isSelected
		else:
			self.profile.encryptDirNames = isSelected

	def _setSalt(self, button):

		if self.profile.type == EncryptionType.GDRIVE:
			saltPath = self.dialog.browse(1, self.settings.getLocalizedString(30110), "")

			if not saltPath:
				return

			with open(saltPath, "r") as file:
				salt = file.read()

		else:
			salt = self.dialog.input(self.settings.getLocalizedString(30110))

		button.setLabel(label2=salt or " ")
		self.profile.salt = salt

	def _setSuffix(self, button):
		suffix = self.dialog.input(self.settings.getLocalizedString(30113))
		button.setLabel(label2=suffix or " ")
		self.profile.suffix = suffix

	def _updateButtonPositions(self):
		self.visibleButtonIDs = [button.getId() for setting, button in self.buttons.items() if button.isVisible()]
		yPosition = 125 + self.buttonSpacing

		for id in self.visibleButtonIDs:
			self.getControl(id).setPosition(self.center, yPosition)
			yPosition += self.buttonHeight

	def _updateList(self, direction):
		currentIndex = self.visibleButtonIDs.index(self.buttonID)

		if direction == "up":
			newIndex = currentIndex - 1
		elif direction == "down":
			newIndex = (currentIndex + 1) % len(self.visibleButtonIDs)

		newButton = self.getControl(self.visibleButtonIDs[newIndex])
		self.setFocus(newButton)

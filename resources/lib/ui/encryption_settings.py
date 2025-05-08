import os

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

	def __init__(self, mode=None, profile=None):
		self.mode = mode
		self.profile = profile or encryption_profiles.GDriveEncryptionProfile()
		self.profileID = profile.id if profile else None
		self.profileManager = ProfileManager()
		self.settings = SETTINGS
		self.dialog = Dialog()
		self.init = True
		self.modified = False
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
			else:
				self.setFocus(self.buttons[0]["button"])

		elif action == self.ACTION_MOVE_DOWN:

			if self.buttonID == self.visibleButtonIDs[-1]:
				self.setFocus(self.buttonOK)
			elif self.buttonID in (self.buttonCloseID, self.buttonOKid):
				self.setFocusId(self.visibleButtonIDs[0])
			elif self.buttonID in self.visibleButtonIDs:
				self._updateList("down")
			else:
				self.setFocus(self.buttons[0]["button"])

		elif action == self.ACTION_MOVE_RIGHT:

			if self.buttonID in self.visibleButtonIDs or self.buttonID == self.buttonOKid:
				self.setFocus(self.buttonClose)
			elif self.buttonID == self.buttonCloseID:
				self.setFocusId(self.visibleButtonIDs[0])
			else:
				self.setFocus(self.buttons[0]["button"])

		elif action == self.ACTION_MOVE_LEFT:

			if self.buttonID in self.visibleButtonIDs or self.buttonID == self.buttonCloseID:
				self.setFocus(self.buttonOK)
			elif self.buttonID == self.buttonOKid:
				self.setFocusId(self.visibleButtonIDs[0])
			else:
				self.setFocus(self.buttons[0]["button"])

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

	def _addBackground(self):
		backgroundFade = self._addControlImage(0, 0, self.viewportWidth, self.viewportHeight, self.blackTexture, colorDiffuse="CCFFFFFF")
		backgroundInvis = self._addControlButton(0, 0, self.viewportWidth, self.viewportHeight, focusTexture="", noFocusTexture="")
		self.backgroundGrayGdrive = self._addControlButton(
			self.x,
			self.y,
			self.windowWidth,
			int(self.buttonHeight * len(self.gdriveButtons) + self.buttonSpacing + 100),
			focusTexture=self.grayTexture,
			noFocusTexture=self.grayTexture,
		)
		self.backgroundGrayRclone = self._addControlButton(
			self.x,
			self.y,
			self.windowWidth,
			int(self.buttonHeight * (len(self.rcloneButtons) - 1) + self.buttonSpacing + 100),
			focusTexture=self.grayTexture,
			noFocusTexture=self.grayTexture,
		)
		self.backgroundDarkGrayGdrive = self._addControlImage(
			self.center - 5,
			185 + self.buttonSpacing,
			self.buttonWidth + 10,
			self.buttonHeight * len(self.gdriveButtons) + 10,
			self.dGrayTexture,
		)
		self.backgroundDarkGrayRcloneState1 = self._addControlImage(
			self.center - 5,
			185,
			self.buttonWidth + 10,
			self.buttonHeight * (len(self.rcloneButtons) - 1) + 10,
			self.dGrayTexture,
		)
		self.backgroundDarkGrayRcloneState2 = self._addControlImage(
			self.center - 5,
			185,
			self.buttonWidth + 10,
			self.buttonHeight * (len(self.rcloneButtons) - 2) + 10,
			self.dGrayTexture,
		)
		self.bar = self._addControlButton(
			self.x,
			self.y,
			self.windowWidth,
			40,
			f"[B]{self.settings.getLocalizedString(30123)}[/B]",
			focusTexture=self.blueTexture,
			noFocusTexture=self.blueTexture,
			textOffsetX=20,
			shadowColor="0xFF000000",
		)
		self.addControls(
			[
				backgroundFade,
				backgroundInvis,
				self.backgroundGrayGdrive,
				self.backgroundGrayRclone,
				self.backgroundDarkGrayGdrive,
				self.backgroundDarkGrayRcloneState1,
				self.backgroundDarkGrayRcloneState2,
				self.bar,
			]
		)
		self.backgroundID = backgroundInvis.getId()

	def _addControlButton(self, x, y, width, height, label="", focusTexture=None, noFocusTexture=None, **kwargs):
		focusTexture = self.focusTexture if focusTexture is None else focusTexture
		noFocusTexture = self.dGrayTexture if noFocusTexture is None else noFocusTexture
		return xbmcgui.ControlButton(
			x,
			y,
			width,
			height,
			label,
			focusTexture=focusTexture,
			noFocusTexture=noFocusTexture,
			**kwargs,
		)

	def _addControlImage(self, x, y, width, height, filename, **kwargs):
		return xbmcgui.ControlImage(
			x,
			y,
			width,
			height,
			filename,
			**kwargs,
		)

	def _addControlEdit(self, label):
		return xbmcgui.ControlEdit(
			0,
			0,
			self.buttonWidth,
			self.buttonHeight,
			f"{label}",
			focusTexture=self.focusTexture,
			noFocusTexture=self.dGrayTexture,
			_alignment=4,
		)

	def _addControlRadioButton(self, label):
		return xbmcgui.ControlRadioButton(
			0,
			0,
			self.buttonWidth,
			self.buttonHeight,
			label,
			noFocusOffTexture=self.focusOffTexture,
			focusOffTexture=self.focusOffTexture,
			focusOnTexture=self.focusOnTexture,
			noFocusOnTexture=self.focusOnTexture,
			focusTexture=self.focusTexture,
			noFocusTexture=self.dGrayTexture,
			textOffsetX=0,
			_alignment=4,
		)

	def _calculateDimensions(self, buttonAmount):
		self.viewportWidth = self.getWidth()
		self.viewportHeight = self.getHeight()
		self.windowWidth = int(1000 * self.viewportWidth / 1920)
		self.buttonWidth = self.windowWidth - 54
		self.buttonHeight = 40
		self.buttonSpacing = 60
		self.windowHeight = int(self.buttonHeight * buttonAmount + self.buttonSpacing + 100)
		self.windowBottom = int((self.viewportHeight + self.windowHeight) / 2)
		self.x = int((self.viewportWidth - self.windowWidth) / 2)
		self.y = int((self.viewportHeight - self.windowHeight) / 2)
		self.center = int(self.x + (self.windowWidth - self.buttonWidth) / 2)

	def _createButtons(self):
		self.profileNameButton = {"type": "edit", "label": SETTINGS.getLocalizedString(30107), "setting": "profile_name", "function": self._setProfileName}
		self.gdriveButtons = [
			{"type": "push", "label": SETTINGS.getLocalizedString(30108), "setting": "encryption_type", "function": self._setEncryptionType},
			{"type": "edit", "label": SETTINGS.getLocalizedString(30109), "setting": "password", "function": self._setPassword},
			{"type": "push", "label": SETTINGS.getLocalizedString(30110), "setting": "salt", "function": self._setSalt},
			{"type": "radio", "label": SETTINGS.getLocalizedString(30115), "setting": "encrypt_dir_names", "function": self._setEncryptDirNames},
		]
		self.rcloneButtons = [
			{"type": "push", "label": SETTINGS.getLocalizedString(30108), "setting": "encryption_type", "function": self._setEncryptionType},
			{"type": "edit", "label": SETTINGS.getLocalizedString(30109), "setting": "password", "function": self._setPassword},
			{"type": "edit", "label": SETTINGS.getLocalizedString(30110), "setting": "salt", "function": self._setSalt},
			{"type": "push", "label": SETTINGS.getLocalizedString(30111), "setting": "filename_encryption", "function": self._setFilenameEncryption},
			{"type": "push", "label": SETTINGS.getLocalizedString(30112), "setting": "filename_encoding", "function": self._setFilenameEncoding},
			{"type": "edit", "label": SETTINGS.getLocalizedString(30113), "setting": "suffix", "function": self._setSuffix},
			{"type": "radio", "label": SETTINGS.getLocalizedString(30114), "setting": "encrypt_data", "function": self._setEncryptData},
			{"type": "radio", "label": SETTINGS.getLocalizedString(30115), "setting": "encrypt_dir_names", "function": self._setEncryptDirNames},
		]
		self.buttons = [self.profileNameButton] + self.gdriveButtons + self.rcloneButtons
		buttonAmount = len(self.gdriveButtons) if self.profile.type == EncryptionType.GDRIVE else len(self.rcloneButtons) - 1
		self._calculateDimensions(buttonAmount)
		buttons = []

		for button in self.buttons:
			type = button["type"]

			if type == "push":
				button["button"] = self._addControlButton(0, 0, self.buttonWidth, self.buttonHeight, button["label"], textOffsetX=0, alignment=4)
			elif type == "edit":
				button["button"] = self._addControlEdit(button["label"])
			elif type == "radio":
				button["button"] = self._addControlRadioButton(button["label"])

			buttons.append(button["button"])

		self.gdriveButtons.insert(0, self.profileNameButton)
		self.rcloneButtons.insert(0, self.profileNameButton)
		self._addBackground()
		self.buttonOK = self._addControlButton(
			self.center,
			self.windowBottom - 60,
			100,
			self.buttonHeight,
			self.settings.getLocalizedString(30066),
			alignment=2 + 4,
		)
		self.buttonClose = self._addControlButton(
			self.center + 120,
			self.windowBottom - 60,
			100,
			self.buttonHeight,
			self.settings.getLocalizedString(30067),
			alignment=2 + 4,
		)
		self.addControls(buttons + [self.buttonOK, self.buttonClose])
		self.buttonCloseID = self.buttonClose.getId()
		self.buttonOKid = self.buttonOK.getId()
		self.buttonHandlers = {button["button"].getId(): button["function"] for button in self.buttons}
		self._setLabels()
		self.init = False
		self._resetButtonsVisibility()
		self.setFocusId(self.visibleButtonIDs[0])

	def _displayNotification(self):

		if self.mode == "add":
			self.dialog.notification(30124)
		else:
			self.dialog.notification(30125)

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
			settingsVisible += ["encrypt_dir_names"]
			settingsInvisible = ["filename_encryption", "filename_encoding", "suffix", "encrypt_data"]
			self.backgroundDarkGrayRcloneState1.setVisible(False)
			self.backgroundDarkGrayRcloneState2.setVisible(False)
			[button["button"].setVisible(False) for button in self.rcloneButtons]
		else:
			settingsVisible += ["filename_encryption", "encrypt_data"]

			if self.profile.filenameEncryption == "off":
				settingsVisible += ["suffix"]
				settingsInvisible = ["filename_encoding", "encrypt_dir_names"]
				self.backgroundDarkGrayRcloneState1.setVisible(False)
				self.backgroundDarkGrayRcloneState2.setVisible(True)
			else:
				settingsVisible += ["filename_encoding", "encrypt_dir_names"]
				settingsInvisible = ["suffix"]
				self.backgroundDarkGrayRcloneState1.setVisible(True)

			[button["button"].setVisible(False) for button in self.gdriveButtons]

		self._setButtonsVisibility(settingsVisible, True)
		self._setButtonsVisibility(settingsInvisible, False)
		self._updateButtonPositions()

	def _saveProfile(self):
		[button["function"](button["button"]) for button in self.buttons if button["type"] == "edit"]

		if not self.profile.name:
			self.dialog.ok(30126)
			return
		elif not self.profile.password:
			self.dialog.ok(30127)
			return
		elif self.profile.type == EncryptionType.GDRIVE and not self.profile.salt:
			self.dialog.ok(30128)
			return

		if self.mode == "add":
			self.profileManager.addProfile(self.profile)
		else:
			self.profile.id = self.profileID
			self.profileManager.updateProfile(self.profile)
			self.modified = True

		return True

	def _setButtonsVisibility(self, settings, visible):
		buttons = self.gdriveButtons if self.profile.type == EncryptionType.GDRIVE else self.rcloneButtons
		[button["button"].setVisible(visible) for button in buttons if button["setting"] in settings]

	def _setEncryptData(self, button):
		self.profile.encryptData = button.isSelected()

	def _setEncryptDirNames(self, button):
		self.profile.encryptDirNames = button.isSelected()

	def _setEncryptionType(self, button):
		encryptionTypes = [EncryptionType.GDRIVE.value, EncryptionType.RCLONE.value]
		selection = self.dialog.select(30108, encryptionTypes)

		if selection == -1:
			return

		type = encryptionTypes[selection]
		button.setLabel(label2=type)
		type = EncryptionType[type.upper()]
		self._setProfile(type=type)
		self._setLabels()
		self._resetButtonsVisibility()
		self.setFocus(self.gdriveButtons[1]["button"] if type == EncryptionType.GDRIVE else self.rcloneButtons[1]["button"])

	def _setFilenameEncoding(self, button):
		encodingTypes = ["base32", "base64", "base32768"]
		selection = self.dialog.select(30112, encodingTypes)

		if selection == -1:
			return

		type = encodingTypes[selection]
		button.setLabel(label2=type)
		self.profile.filenameEncoding = type

	def _setFilenameEncryption(self, button):
		encryptionTypes = ["standard", "obfuscate", "off"]
		selection = self.dialog.select(30111, encryptionTypes)

		if selection == -1:
			return

		type = encryptionTypes[selection]
		button.setLabel(label2=type)
		self.profile.filenameEncryption = type
		settingsVisible = ["profile_name", "encryption_type", "password", "salt", "filename_encryption", "encrypt_data"]

		if type == "off":
			settingsVisible += ["suffix"]
			settingsInvisible = ["filename_encoding", "encrypt_dir_names"]
			self.backgroundDarkGrayRcloneState1.setVisible(False)
			self.backgroundDarkGrayRcloneState2.setVisible(True)
		else:
			settingsVisible += ["filename_encoding", "encrypt_dir_names"]
			settingsInvisible = ["suffix"]
			self.backgroundDarkGrayRcloneState1.setVisible(True)

		self._setButtonsVisibility(settingsInvisible, False)
		self._setButtonsVisibility(settingsVisible, True)
		self._updateButtonPositions()

	def _setLabels(self):

		if not self.init:
			self.profile.name = self.profileNameButton["button"].getText()

		settings = {
			"profile_name": self.profile.name,
			"encryption_type": self.profile.type.value,
			"password": self.profile.password,
			"salt": self.profile.salt,
			"encrypt_dir_names": self.profile.encryptDirNames,
		}

		if self.profile.type == EncryptionType.GDRIVE:
			self.buttons = self.gdriveButtons
		else:
			settings.update(
				{
					"filename_encryption": self.profile.filenameEncryption,
					"filename_encoding": self.profile.filenameEncoding,
					"suffix": self.profile.suffix,
					"encrypt_data": self.profile.encryptData,
				}
			)
			self.buttons = self.rcloneButtons

		for button in self.buttons:
			type = button["type"]

			if type == "push":
				button["button"].setLabel(label2=settings[button["setting"]])
			elif type == "edit":
				button["button"].setText(settings[button["setting"]])
			elif type == "radio":
				button["button"].setSelected(settings[button["setting"]])

	def _setPassword(self, button):
		self.profile.password = button.getText()

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
		self.profile.name = button.getText()

	def _setSalt(self, button):

		if self.profile.type == EncryptionType.GDRIVE:
			saltPath = self.dialog.browse(1, 30110, "")

			if not saltPath:
				return

			with open(saltPath, "r") as file:
				salt = file.read()

			button.setLabel(label2=salt or " ")
		else:
			salt = button.getText()

		self.profile.salt = salt

	def _setSuffix(self, button):
		self.profile.suffix = button.getText()

	def _updateButtonPositions(self):

		if self.profile.type == EncryptionType.GDRIVE:
			buttons = self.gdriveButtons
			self._calculateDimensions(len(self.gdriveButtons))
			self.backgroundGrayGdrive.setPosition(self.x, self.y)
			self.backgroundGrayRclone.setVisible(False)
		else:
			buttons = self.rcloneButtons
			self._calculateDimensions(len(self.rcloneButtons) - 1)
			self.backgroundGrayRclone.setPosition(self.x, self.y)
			self.backgroundGrayRclone.setVisible(True)

		self.bar.setPosition(self.x, self.y)
		self.visibleButtonIDs = [button["button"].getId() for button in buttons if button["button"].isVisible()]
		yPosition = self.y + 70

		for id in self.visibleButtonIDs:
			self.getControl(id).setPosition(self.center, yPosition)
			yPosition += self.buttonHeight

		self.buttonOK.setPosition(self.center, self.windowBottom - 60)
		self.buttonClose.setPosition(self.center + 120, self.windowBottom - 60)

	def _updateList(self, direction):
		currentIndex = self.visibleButtonIDs.index(self.buttonID)

		if direction == "up":
			newIndex = currentIndex - 1
		elif direction == "down":
			newIndex = (currentIndex + 1) % len(self.visibleButtonIDs)

		newButton = self.getControl(self.visibleButtonIDs[newIndex])
		self.setFocus(newButton)

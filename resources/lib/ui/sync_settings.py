import os

import xbmcgui
import xbmcaddon


class SyncOptions(xbmcgui.WindowDialog):
	ACTION_MOVE_LEFT = 1
	ACTION_MOVE_RIGHT = 2
	ACTION_MOVE_UP = 3
	ACTION_MOVE_DOWN = 4
	ACTION_SELECT_ITEM = 7
	ACTION_BACKSPACE = 92

	def __init__(self, *args, **kwargs):
		self.syncStartup = kwargs.get("startup_sync")
		self.closed = False
		addon = xbmcaddon.Addon()
		self.dialog = xbmcgui.Dialog()
		textures = os.path.join(addon.getAddonInfo("path"), "resources", "lib", "textures")
		windowTextures = os.path.join(textures, "AddonWindow")
		radioButtonTextures = os.path.join(textures, "RadioButton")
		self.radioButtonFocus = os.path.join(radioButtonTextures, "radiobutton-focus.png")
		self.radioButtonNoFocus = os.path.join(radioButtonTextures, "radiobutton-nofocus.png")
		self.radioButtonMenuNoFocus = os.path.join(radioButtonTextures, "MenuItemNF.png")
		self.radioButtonMenuFocus = os.path.join(radioButtonTextures, "MenuItemFO.png")

		buttonTextures = os.path.join(textures, "Button")
		self.buttonNoFocus = os.path.join(buttonTextures, "KeyboardKeyNF.png")
		self.buttonFocus = os.path.join(buttonTextures, "KeyboardKey.png")
		self.blueTexture = os.path.join(windowTextures, "dialogheader.png")
		self.grayTexture = os.path.join(windowTextures, "ContentPanel.png")

		viewportWidth = self.getWidth()
		viewportHeight = self.getHeight()

		self.windowWidth = int(1000 * viewportWidth / 1920)
		self.windowHeight = int(700 * viewportHeight / 1080)
		self.windowBottom = int((viewportHeight + self.windowHeight) / 2)

		self.x = int((viewportWidth - self.windowWidth) / 2)
		self.y = int((viewportHeight - self.windowHeight) / 2)

		self.buttonWidth = self.windowWidth - 20
		self.center = int((self.x + self.windowWidth / 2) - (self.buttonWidth / 2))

		background = xbmcgui.ControlImage(self.x, self.y, self.windowWidth, self.windowHeight, self.grayTexture)
		bar = xbmcgui.ControlImage(self.x, self.y, self.windowWidth, 40, self.blueTexture)
		label = xbmcgui.ControlLabel(self.x + 10, self.y + 5, 0, 0, "Sync Settings")
		self.addControls([background, bar, label])
		self.createButtons()

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
			self.closed = True
			self.close()
		elif self.buttonID == self.buttonOKID:
			self.settings = {}
			settings = {
				"Sync at startup?": "startup_sync",
				"Does this folder contain encrypted files?": "contains_encrypted",
				"Rename videos to a Kodi friendly format?": "file_renaming",
				"Create a Kodi friendly directory structure?": "folder_structure",
				"Sync NFOs?": "sync_nfos",
				"Sync Subtitles?": "sync_subtitles",
				"Sync Fanart/Posters?": "sync_artwork",
			}

			for index, button in enumerate(self.menuButtons):
				label = self.buttonLabels[index]
				selected = button.isSelected()
				self.settings[settings[label]] = selected

			self.close()

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

	def createButtons(self):
		spacing = 60
		buttonWidth = 100
		buttonHeight = 30
		font = "font13"

		self.buttonOK = xbmcgui.ControlButton(
			x=self.x + 20,
			y=self.windowBottom - 50,
			width=buttonWidth,
			height=buttonHeight,
			label="OK",
			font=font,
			noFocusTexture=self.radioButtonMenuNoFocus,
			focusTexture=self.radioButtonMenuFocus,
		)
		self.buttonClose = xbmcgui.ControlButton(
			x=self.x + 80 + 50,
			y=self.windowBottom - 50,
			width=buttonWidth,
			height=buttonHeight,
			label="Close",
			font=font,
			noFocusTexture=self.radioButtonMenuNoFocus,
			focusTexture=self.radioButtonMenuFocus,
		)
		self.buttonLabels = [
			"Does this folder contain encrypted files?",
			"Rename videos to a Kodi friendly format?",
			"Create a Kodi friendly directory structure?",
			"Sync NFOs?",
			"Sync Subtitles?",
			"Sync Fanart/Posters?",
		]

		if self.syncStartup:
			self.buttonLabels.insert(0, "Sync at startup?")

		self.menuButtons = []

		for buttonLabel in self.buttonLabels:
			self.menuButtons.append(
				xbmcgui.ControlRadioButton(
					x=self.center,
					y=self.y + spacing,
					width=self.buttonWidth,
					height=buttonHeight,
					label=buttonLabel,
					font=font,
					noFocusOffTexture=self.radioButtonNoFocus,
					focusOffTexture=self.radioButtonNoFocus,
					focusOnTexture=self.radioButtonFocus,
					noFocusOnTexture=self.radioButtonFocus,
					focusTexture=self.radioButtonMenuFocus,
					noFocusTexture=self.radioButtonMenuNoFocus,
				)
			)
			spacing += 40

		actionButtons = [self.buttonOK, self.buttonClose]
		self.addControls(actionButtons + self.menuButtons)
		self.menuButtonIDs = [button.getId() for button in self.menuButtons]
		self.buttonCloseID = self.buttonClose.getId()
		self.buttonOKID = self.buttonOK.getId()
		self.setFocusId(self.menuButtonIDs[0])

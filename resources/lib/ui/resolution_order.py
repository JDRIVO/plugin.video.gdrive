import os
import time

import xbmcgui
import xbmcaddon

from constants import SETTINGS


class ResolutionOrder(xbmcgui.WindowDialog):
	ACTION_MOVE_LEFT = 1
	ACTION_MOVE_RIGHT = 2
	ACTION_MOVE_UP = 3
	ACTION_MOVE_DOWN = 4
	ACTION_SELECT_ITEM = 7
	ACTION_PREVIOUS_MENU = 10
	ACTION_BACKSPACE = 92
	ACTION_MOUSE_LEFT_CLICK = 100
	ACTION_MOUSE_RIGHT_CLICK = 101
	ACTION_TOUCH_TAP = 401

	def __init__(self, *args, **kwargs):
		self.resolutions = kwargs["resolutions"]
		self.settings = SETTINGS
		self.shift = False
		self.closed = False
		self.lastUpdate = 0
		self.buttonWidth = 120
		self.buttonHeight = 30
		self.buttonAmount = len(self.resolutions)
		self.font = "font14"
		self._initializePaths()
		self._calculateViewport()
		self._addBackground()
		self._createButtons()

	def onAction(self, action):
		action = action.getId()
		self.focusedButtonID = self.getFocusId()

		if action in (self.ACTION_PREVIOUS_MENU, self.ACTION_BACKSPACE):
			self.closed = True
			self.close()
		elif action == self.ACTION_MOVE_UP:

			if self.focusedButtonID in self.buttonIDs:
				self._updateList("up")
			elif self.focusedButtonID == self.buttonOKid:
				self.setFocus(self.buttonClose)
			elif self.focusedButtonID == self.buttonCloseID:
				self.setFocus(self.buttonOK)
			else:
				self.setFocusId(self.buttonIDs[0])

		elif action == self.ACTION_MOVE_DOWN:

			if self.focusedButtonID in self.buttonIDs:
				self._updateList("down")
			elif self.focusedButtonID == self.buttonOKid:
				self.setFocus(self.buttonClose)
			elif self.focusedButtonID == self.buttonCloseID:
				self.setFocus(self.buttonOK)
			else:
				self.setFocusId(self.buttonIDs[0])

		elif action in (self.ACTION_MOVE_RIGHT, self.ACTION_MOVE_LEFT):
			self.shift = False
			self._getButton(self.focusedButtonID).setLabel(focusedColor="0xFFFFFFFF")

			if self.focusedButtonID in self.buttonIDs:
				self.setFocus(self.buttonOK)
			else:
				self.setFocusId(self.buttonIDs[0])

		elif action == self.ACTION_SELECT_ITEM:
			self.shift = self.shift == False
			button = self._getButton(self.focusedButtonID)

			if self.shift:
				button.setLabel(focusedColor="0xFFFFB70F")
			else:
				button.setLabel(focusedColor="0xFFFFFFFF")

			self.setFocus(button)

		elif action in (self.ACTION_MOUSE_LEFT_CLICK, self.ACTION_TOUCH_TAP):

			if self.focusedButtonID in self.buttonIDs:
				self.shift = True
				self._updateList("down", setFocus=False)

		elif action == self.ACTION_MOUSE_RIGHT_CLICK:

			if self.focusedButtonID in self.buttonIDs:
				self.shift = True
				self._updateList("up", setFocus=False)

	def onControl(self, control):
		self.focusedButtonID = control.getId()

		if self.focusedButtonID in (self.backgroundID, self.buttonCloseID):
			self.closed = True
			self.close()
		elif self.focusedButtonID == self.buttonOKid:
			self.resolutions = [button.getLabel() for button in self.buttons]
			self.close()

	def _addBackground(self):
		backgroundInvis = xbmcgui.ControlButton(0, 0, self.viewportWidth, self.viewportHeight, "", focusTexture="", noFocusTexture="")
		background = xbmcgui.ControlButton(self.x, self.y, self.windowWidth, self.windowHeight, "", focusTexture=self.grayTexture, noFocusTexture=self.grayTexture)
		# ControlImage needed to overcome bug that prevents window from closing
		_ = xbmcgui.ControlImage(self.x, self.y, self.windowWidth, 40, self.blueTexture)
		bar = xbmcgui.ControlButton(self.x, self.y, self.windowWidth, 40, f"[B]{self.settings.getLocalizedString(30083)}[/B]", focusTexture=self.blueTexture, noFocusTexture=self.blueTexture, shadowColor="0xFF000000", textOffsetX=20)
		self.addControls([backgroundInvis, background, _, bar])
		self.backgroundID = backgroundInvis.getId()

	def _addControlButton(self, x, y, buttonWidth, buttonHeight, label=""):
		button = xbmcgui.ControlButton(
			x,
			y,
			buttonWidth,
			buttonHeight,
			label,
			noFocusTexture=self.dGrayTexture,
			focusTexture=self.focusTexture,
			font=self.font,
			alignment=2 + 4,
		)
		return button

	def _calculateViewport(self):
		self.viewportWidth = self.getWidth()
		self.viewportHeight = self.getHeight()
		self.windowWidth = int(350 * self.viewportWidth / 1920)
		self.windowHeight = int(350 * self.viewportHeight / 1080)
		self.x = (self.viewportWidth - self.windowWidth) // 2
		self.y = (self.viewportHeight - self.windowHeight) // 2

	def _createButtons(self):
		y = 60
		self.buttons = [self._addControlButton(self.x + 10, self.y + y + 30 * i, self.buttonWidth, self.buttonHeight, res) for i, res in enumerate(self.resolutions)]
		self.buttonOK = self._addControlButton(self.x + self.buttonWidth + 20, self.y + y, 80, self.buttonHeight, self.settings.getLocalizedString(30066))
		self.buttonClose = self._addControlButton(self.x + self.buttonWidth + 20, self.y + y + 35, 80, self.buttonHeight, label=self.settings.getLocalizedString(30084))
		self.addControls(self.buttons + [self.buttonOK, self.buttonClose])
		self.buttonIDs = [button.getId() for button in self.buttons]
		self.buttonCloseID = self.buttonClose.getId()
		self.buttonOKid = self.buttonOK.getId()
		self.setFocusId(self.buttonIDs[0])

	def _getButton(self, buttonID):
		return self.getControl(buttonID)

	def _initializePaths(self):
		mediaPath = os.path.join(xbmcaddon.Addon().getAddonInfo("path"), "resources", "media")
		self.blueTexture = os.path.join(mediaPath, "blue.png")
		self.grayTexture = os.path.join(mediaPath, "gray.png")
		self.dGrayTexture = os.path.join(mediaPath, "dgray.png")
		self.focusTexture = os.path.join(mediaPath, "focus.png")

	def _updateList(self, direction, setFocus=True):
		currentTime = time.time()

		if currentTime - self.lastUpdate < 0.05:
			return

		self.lastUpdate = currentTime
		currentIndex = self.buttonIDs.index(self.focusedButtonID)

		if direction == "up":
			newIndex = currentIndex - 1
		elif direction == "down":
			newIndex = (currentIndex + 1) % self.buttonAmount

		newButton = self.buttons[newIndex]

		if self.shift:
			labels = [button.getLabel() for button in self.buttons]

			if currentIndex == 0 and direction == "up":
				labels = labels[1:] + [labels[0]]
			elif currentIndex == self.buttonAmount - 1 and direction == "down":
				labels = [labels[-1]] + labels[:-1]
			else:
				labels[currentIndex], labels[newIndex] = labels[newIndex], labels[currentIndex]

			[button.setLabel(labels[idx]) for idx, button in enumerate(self.buttons)]

			if setFocus:
				self.buttons[currentIndex].setLabel(focusedColor="0xFFFFFFFF")
				newButton.setLabel(focusedColor="0xFFFFB70F")

		if setFocus:
			self.setFocus(newButton)

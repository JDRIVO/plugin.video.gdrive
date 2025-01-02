import os

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
		self.priorityList = None
		self.shift = False
		self.buttonWidth = 120
		self.buttonHeight = 30
		self.font = "font14"
		self._initializePaths()
		self._calculateViewport()
		self._addBackground()
		self._addLabels()
		self._createButtons()

	def onAction(self, action):
		action = action.getId()
		self.buttonID = self.getFocusId()

		if action in (self.ACTION_PREVIOUS_MENU, self.ACTION_BACKSPACE):
			self.close()
		elif action == self.ACTION_MOVE_UP:

			if self.buttonID in self.buttonIDs:
				self._updateList("up")
			else:

				if self.buttonID == self.buttonOKid:
					self.setFocus(self.buttonClose)
				else:
					self.setFocus(self.buttonOK)

		elif action == self.ACTION_MOVE_DOWN:

			if self.buttonID in self.buttonIDs:
				self._updateList("down")
			else:

				if self.buttonID == self.buttonOKid:
					self.setFocus(self.buttonClose)
				else:
					self.setFocus(self.buttonOK)

		elif action in (self.ACTION_MOVE_RIGHT, self.ACTION_MOVE_LEFT):
			self.shift = False

			if self.buttonID in self.buttonIDs:
				self.setFocus(self.buttonOK)
			else:
				self.setFocusId(self.buttonIDs[0])

		elif action == self.ACTION_SELECT_ITEM:
			self.shift = self.shift == False

		elif action in (self.ACTION_MOUSE_LEFT_CLICK, self.ACTION_TOUCH_TAP):

			if self.buttonID in self.buttonIDs:
				self.shift = True
				self._updateList("down", setFocus=False)

		elif action == self.ACTION_MOUSE_RIGHT_CLICK:

			if self.buttonID in self.buttonIDs:
				self.shift = True
				self._updateList("up", setFocus=False)

	def onControl(self, control):
		self.buttonID = control.getId()

		if self.buttonID in (self.backgroundID, self.buttonCloseID):
			self.close()
		elif self.buttonID == self.buttonOKid:
			self.priorityList = [self._getLabel(button) for button in self.buttonIDs]
			self.close()

	def _addBackground(self):
		backgroundInvis = xbmcgui.ControlButton(0, 0, self.viewportWidth, self.viewportHeight, "", focusTexture="", noFocusTexture="")
		background = xbmcgui.ControlButton(self.x, self.y, self.w, self.h, "", focusTexture=self.grayTexture, noFocusTexture=self.grayTexture)
		bar = xbmcgui.ControlImage(self.x, self.y, self.w, 40, self.blueTexture)
		self.addControls([backgroundInvis, background, bar])
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

	def _addLabels(self):
		labelTitle = xbmcgui.ControlLabel(self.x + 20, self.y + 5, 0, 0, f"[B]{self.settings.getLocalizedString(30083)}[/B]")
		labelTitleShadow = xbmcgui.ControlLabel(self.x + 20, self.y + 6, 0, 0, f"[B][COLOR black]{self.settings.getLocalizedString(30083)}[/COLOR][/B]")
		self.addControls([labelTitleShadow, labelTitle])

	def addShiftableButtons(self, y):
		buttons = []

		for res in self.resolutions:
			buttons.append(self._addControlButton(self.x + 10, self.y + y, self.buttonWidth, self.buttonHeight, res))
			y += 30

		return buttons

	def _calculateViewport(self):
		self.viewportWidth = self.getWidth()
		self.viewportHeight = self.getHeight()
		self.w = int(350 * self.viewportWidth / 1920)
		self.h = int(350 * self.viewportHeight / 1080)
		self.x = (self.viewportWidth - self.w) // 2
		self.y = (self.viewportHeight - self.h) // 2

	def _createButtons(self):
		y = 60
		shiftableButtons = self.addShiftableButtons(y)
		self.buttonOK = self._addControlButton(self.x + self.buttonWidth + 20, self.y + y, 80, self.buttonHeight, self.settings.getLocalizedString(30066))
		self.buttonClose = self._addControlButton(self.x + self.buttonWidth + 20, self.y + y + 35, 80, self.buttonHeight, label=self.settings.getLocalizedString(30084))
		self.addControls(shiftableButtons + [self.buttonOK, self.buttonClose])
		self.buttonIDs = [button.getId() for button in shiftableButtons]
		self.buttonCloseID = self.buttonClose.getId()
		self.buttonOKid = self.buttonOK.getId()
		self.setFocusId(self.buttonIDs[0])

	def _getButton(self, buttonID):
		return self.getControl(buttonID)

	def _getLabel(self, buttonID):
		return self._getButton(buttonID).getLabel()

	def _initializePaths(self):
		mediaPath = os.path.join(xbmcaddon.Addon().getAddonInfo("path"), "resources", "media")
		self.blueTexture = os.path.join(mediaPath, "blue.png")
		self.grayTexture = os.path.join(mediaPath, "gray.png")
		self.dGrayTexture = os.path.join(mediaPath, "dgray.png")
		self.focusTexture = os.path.join(mediaPath, "focus.png")

	def _updateList(self, direction, setFocus=True):
		currentIndex = self.buttonIDs.index(self.buttonID)

		if direction == "up":
			newIndex = currentIndex - 1
		elif direction == "down":
			newIndex = currentIndex + 1

			if newIndex == len(self.buttonIDs):
				newIndex = 0

		currentButton = self._getButton(self.buttonIDs[currentIndex])
		newButton = self._getButton(self.buttonIDs[newIndex])

		if self.shift:

			if currentIndex == 0 and direction == "up":
				labels = [self._getLabel(button) for button in self.buttonIDs[1:]] + [self._getLabel(self.buttonIDs[0])]
				[self._getButton(buttonID).setLabel(labels[index]) for index, buttonID in enumerate(self.buttonIDs)]
			elif currentIndex == len(self.buttonIDs) - 1 and direction == "down":
				labels = [self._getLabel(self.buttonIDs[-1])] + [self._getLabel(button) for button in self.buttonIDs[:-1]]
				[self._getButton(buttonID).setLabel(labels[index]) for index, buttonID in enumerate(self.buttonIDs)]
			else:
				currentButtonName = currentButton.getLabel()
				newButtonName = newButton.getLabel()
				currentButton.setLabel(newButtonName)
				newButton.setLabel(currentButtonName)

		if setFocus:
			self.setFocus(newButton)

import os

import xbmcgui
import xbmcaddon

from constants import SETTINGS


class StrmAffixer(xbmcgui.WindowDialog):
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
	ACTION_TOUCH_LONGPRESS = 411

	def __init__(self, *args, **kwargs):
		self.title = kwargs["title"]
		self.excluded = kwargs["excluded"]
		self.included = kwargs["included"]
		self.settings = SETTINGS
		self.shift = False
		self.closed = False
		self.font = "font14"
		self.buttonWidth = 120
		self.buttonHeight = 30
		self.buttonAmount = len(self.excluded) + len(self.included)
		self._initializePaths()
		self._calculateViewport()
		self._addBackground()
		self._addLabels()
		self._createButtons()

	def onAction(self, action):
		action = action.getId()
		self.buttonID = self.getFocusId()

		if action in (self.ACTION_PREVIOUS_MENU, self.ACTION_BACKSPACE):
			self.closed = True
			self.close()
		elif action == self.ACTION_MOVE_UP:

			if self.buttonID in self.excludedButtonIDs:
				self._updateList("up", self.excludedButtonIDs)
			elif self.buttonID in self.includedButtonIDs:
				self._updateList("up", self.includedButtonIDs)
			elif self.buttonID == self.buttonOKid:

				if self.excludedButtons[0].isVisible():
					self.setFocus(self.excludedButtons[0])
				else:
					self.setFocus(self.includedButtons[0])

			elif self.buttonID == self.buttonCloseID:

				if self.includedButtons[0].isVisible():
					self.setFocus(self.includedButtons[0])
				else:
					self.setFocus(self.excludedButtons[0])

		elif action == self.ACTION_MOVE_DOWN:

			if self.buttonID in self.excludedButtonIDs:
				self._updateList("down", self.excludedButtonIDs)
			elif self.buttonID in self.includedButtonIDs:
				self._updateList("down", self.includedButtonIDs)
			elif self.buttonID == self.buttonOKid:
				self.setFocus(self.buttonClose)
			elif self.buttonID == self.buttonCloseID:
				self.setFocus(self.buttonOK)

		elif action == self.ACTION_MOVE_RIGHT:

			if self.buttonID in self.excludedButtonIDs:

				if self.shift:
					self._updateList("right", self.excludedButtonIDs)
				elif self.includedButtons[0].isVisible():
					self.setFocusId(self.includedButtonIDs[0])
				else:
					self.setFocus(self.buttonClose)

			elif self.buttonID in self.includedButtonIDs:
				self.shift = False
				self.setFocus(self.buttonClose)

			elif self.buttonID == self.buttonCloseID:

				if self.includedButtons[0].isVisible():
					self.setFocus(self.includedButtons[0])
				else:
					self.setFocus(self.excludedButtons[0])

			elif self.buttonID == self.buttonOKid:
				self.setFocus(self.buttonClose)

		elif action == self.ACTION_MOVE_LEFT:

			if self.buttonID in self.excludedButtonIDs:
				self.shift = False
				self.setFocus(self.buttonOK)
			elif self.buttonID in self.includedButtonIDs:

				if self.shift:
					self._updateList("left", self.includedButtonIDs)
				elif self.excludedButtons[0].isVisible():
						self.setFocusId(self.excludedButtonIDs[0])
				else:
					self.setFocus(self.buttonOK)

			elif self.buttonID == self.buttonOKid:

				if self.excludedButtons[0].isVisible():
					self.setFocus(self.excludedButtons[0])
				else:
					self.setFocus(self.includedButtons[0])

			elif self.buttonID == self.buttonCloseID:
				self.setFocusId(self.buttonOKid)

		elif action == self.ACTION_SELECT_ITEM:

			if self.buttonID in self.excludedButtonIDs:
				self.shift = True
				self._updateList("right", self.excludedButtonIDs)
			else:
				self.shift = self.shift == False

		elif action in (self.ACTION_MOUSE_LEFT_CLICK, self.ACTION_TOUCH_TAP):

			if not self._getButton(self.buttonID).isVisible():
				return
			elif self.buttonID in self.includedButtonIDs:
					self.shift = True
					self._updateList("left", self.includedButtonIDs, setFocus=False)
			elif self.buttonID in self.excludedButtonIDs:
					self.shift = True
					self._updateList("right", self.excludedButtonIDs, setFocus=False)

		elif action in (self.ACTION_MOUSE_RIGHT_CLICK, self.ACTION_TOUCH_LONGPRESS):

			if not self._getButton(self.buttonID).isVisible():
				return
			elif self.buttonID in self.includedButtonIDs:
				self.shift = True
				self._updateList("down", self.includedButtonIDs, setFocus=False)

	def onControl(self, control):
		self.buttonID = control.getId()

		if self.buttonID in (self.backgroundID, self.buttonCloseID):
			self.closed = True
			self.close()
		elif self.buttonID == self.buttonOKid:
			self.included.clear()
			[self.included.append(self._getLabel(buttonID)) for buttonID in self.includedButtonIDs if self._getButton(buttonID).isVisible()]
			self.close()

	def _addAffixButtons(self, items, buttons, x):
		y = self.y + 85

		for _ in range(self.buttonAmount):
			button = self._addControlButton(x, y, self.buttonWidth, self.buttonHeight)
			button.setVisible(False)
			buttons.append(button)
			y += 30

	def _addBackground(self):
		backgroundInvis = xbmcgui.ControlButton(0, 0, self.viewportWidth, self.viewportHeight, "", focusTexture="", noFocusTexture="")
		background = xbmcgui.ControlButton(self.x, self.y, self.w, self.h, "", focusTexture=self.grayTexture, noFocusTexture=self.grayTexture)
		bar = xbmcgui.ControlButton(self.x, self.y, self.w, 40, f"[B]{self.title}[/B]", focusTexture=self.blueTexture, noFocusTexture=self.blueTexture, shadowColor="0xFF000000", textOffsetX=20)
		excludeBG = xbmcgui.ControlImage(self.x + 11, self.y + 85, self.buttonWidth, self.buttonHeight * self.buttonAmount, self.dGrayTexture)
		includeBG = xbmcgui.ControlImage(self.x + self.buttonWidth + 20, self.y + 85, self.buttonWidth, self.buttonHeight * self.buttonAmount, self.dGrayTexture)
		self.addControls([backgroundInvis, background, bar, includeBG, excludeBG])
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
		labelExclude = xbmcgui.ControlLabel(self.x + 10, self.y + 50, 120, 30, "[COLOR FF0F85A5]Exclude[/COLOR]", alignment=2 + 4)
		labelInclude = xbmcgui.ControlLabel(self.x + 140, self.y + 50, 120, 30, "[COLOR FF0F85A5]Include[/COLOR]", alignment=2 + 4)
		self.addControls([labelExclude, labelInclude])

	def _calculateViewport(self):
		self.viewportWidth = self.getWidth()
		self.viewportHeight = self.getHeight()
		self.w = int(406 * self.viewportWidth / 1920)
		self.h = int(350 * self.viewportHeight / 1080)
		self.x = (self.viewportWidth - self.w) // 2
		self.y = (self.viewportHeight - self.h) // 2

	def _createButtons(self):
		self.excludedButtons = []
		self.includedButtons = []
		self._addAffixButtons(self.excluded, self.excludedButtons, self.x + 11)
		self._addAffixButtons(self.included, self.includedButtons, self.x + self.buttonWidth + 20)

		for button, label in zip(self.excludedButtons, self.excluded):
			button.setLabel(label)
			button.setVisible(True)

		for button, label in zip(self.includedButtons, self.included):
			button.setLabel(label)
			button.setVisible(True)

		self.buttonOK = self._addControlButton(self.x + 40, self.y + 190, 80, self.buttonHeight, label=self.settings.getLocalizedString(30066))
		self.buttonClose = self._addControlButton(self.x + self.buttonWidth + 30, self.y + 190, 80, self.buttonHeight, label=self.settings.getLocalizedString(30084))
		self.addControls(self.includedButtons + self.excludedButtons + [self.buttonOK, self.buttonClose])
		self.buttonOKid = self.buttonOK.getId()
		self.buttonCloseID = self.buttonClose.getId()
		self.excludedButtonIDs = [button.getId() for button in self.excludedButtons]
		self.includedButtonIDs = [button.getId() for button in self.includedButtons]
		self.setFocusId(self.excludedButtonIDs[0]) if self.excludedButtons[0].isVisible() else self.setFocusId(self.includedButtonIDs[0])

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

	def _resetShiftableButtons(self, currentIndex, excluded):

		if excluded:
			buttonsOutgoing = self.excludedButtons
			buttonsIncoming = self.includedButtons
			outgoing = self.excluded
			incoming = self.included
		else:
			buttonsOutgoing = self.includedButtons
			buttonsIncoming = self.excludedButtons
			outgoing = self.included
			incoming = self.excluded

		buttons = buttonsOutgoing[:]
		movedAffix = buttons.pop(currentIndex).getLabel()

		for button, button_ in zip(buttons, buttonsOutgoing):
			button_.setLabel(button.getLabel())

		for button in buttonsOutgoing[::-1]:

			if button.isVisible():
				button.setVisible(False)
				break

		for button in buttonsIncoming:

			if not button.isVisible():
				button.setLabel(movedAffix)
				button.setVisible(True)
				break

		outgoing.remove(movedAffix)
		incoming.append(movedAffix)

	def _updateList(self, direction, list, setFocus=True):
		currentIndex = list.index(self.buttonID)

		if direction == "up":
			newIndex = currentIndex - 1
			newButton = next((self._getButton(button) for button in list[newIndex::-1] if self._getButton(button).isVisible()))

		elif direction == "down":
			newIndex = currentIndex + 1
			newButton = next((self._getButton(button) for button in list[newIndex:] if self._getButton(button).isVisible()), self._getButton(list[0]))

		if self.shift:

			if currentIndex == 0 and direction == "up":
				labels = [self._getLabel(buttonID) for buttonID in list[1:] if self._getButton(buttonID).isVisible()] + [self._getLabel(list[0])]
				[self._getButton(buttonID).setLabel(labels[index]) for index, buttonID in enumerate(list) if self._getButton(buttonID).isVisible()]

			elif currentIndex == len(list) - 1 and direction == "down":
				labels = [self._getLabel(list[-1])] + [self._getLabel(button) for button in list[:-1]]
				[self._getButton(buttonID).setLabel(labels[index]) for index, buttonID in enumerate(list)]

			elif direction == "right" and list == self.excludedButtonIDs:
				self.shift = False
				self._resetShiftableButtons(currentIndex, True)
				currentIndex = max(currentIndex - 1, 0)

				if self.excludedButtons[currentIndex].isVisible():
					newButton = self.excludedButtons[currentIndex]
				else:
					newButton = self.includedButtons[0]

			elif direction == "left" and list == self.includedButtonIDs:
				self.shift = False
				self._resetShiftableButtons(currentIndex, False)
				currentIndex = max(currentIndex - 1, 0)

				if self.includedButtons[currentIndex].isVisible():
					newButton = self.includedButtons[currentIndex]
				else:
					newButton = self.excludedButtons[0]

			else:
				currentButton = self._getButton(list[currentIndex])
				currentButtonName = currentButton.getLabel()
				newButtonName = newButton.getLabel()
				currentButton.setLabel(newButtonName)
				newButton.setLabel(currentButtonName)

		if setFocus:
			self.setFocus(newButton)

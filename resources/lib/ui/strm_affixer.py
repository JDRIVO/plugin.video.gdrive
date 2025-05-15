import os
import time

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
	ACTION_MOUSE_DOUBLE_CLICK = 103
	ACTION_TOUCH_TAP = 401
	ACTION_TOUCH_LONGPRESS = 411

	def __init__(self, *args, **kwargs):
		self.title = kwargs["title"]
		self.excluded = kwargs["excluded"]
		self.included = kwargs["included"]
		self.settings = SETTINGS
		self.shift = False
		self.closed = False
		self.lastUpdate = 0
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
		self.focusedButtonID = self.getFocusId()

		if action in (self.ACTION_PREVIOUS_MENU, self.ACTION_BACKSPACE):
			self.closed = True
			self.close()
		elif action == self.ACTION_MOVE_UP:

			if self.focusedButtonID in self.excludedButtonIDs:
				self._updateList("up", True)
			elif self.focusedButtonID in self.includedButtonIDs:
				self._updateList("up", False)
			elif self.focusedButtonID == self.buttonOKid:

				if self.excludedButtons[0].isVisible():
					self.setFocus(self.excludedButtons[0])
				else:
					self.setFocus(self.includedButtons[0])

			elif self.focusedButtonID == self.buttonCloseID:

				if self.includedButtons[0].isVisible():
					self.setFocus(self.includedButtons[0])
				else:
					self.setFocus(self.excludedButtons[0])

			else:

				if self.excludedButtons[0].isVisible():
					self.setFocus(self.excludedButtons[0])
				else:
					self.setFocus(self.includedButtons[0])

		elif action == self.ACTION_MOVE_DOWN:

			if self.focusedButtonID in self.excludedButtonIDs:
				self._updateList("down", True)
			elif self.focusedButtonID in self.includedButtonIDs:
				self._updateList("down", False)
			elif self.focusedButtonID == self.buttonOKid:
				self.setFocus(self.buttonClose)
			elif self.focusedButtonID == self.buttonCloseID:
				self.setFocus(self.buttonOK)
			else:

				if self.excludedButtons[0].isVisible():
					self.setFocus(self.excludedButtons[0])
				else:
					self.setFocus(self.includedButtons[0])

		elif action == self.ACTION_MOVE_RIGHT:

			if self.focusedButtonID in self.excludedButtonIDs:

				if self.shift:
					self._updateList("right", True)
				elif self.includedButtons[0].isVisible():
					self.setFocusId(self.includedButtonIDs[0])
				else:
					self.setFocus(self.buttonClose)

			elif self.focusedButtonID in self.includedButtonIDs:
				self.shift = False
				self._getButton(self.focusedButtonID).setLabel(focusedColor="0xFFFFFFFF")
				self.setFocus(self.buttonClose)

			elif self.focusedButtonID == self.buttonCloseID:

				if self.includedButtons[0].isVisible():
					self.setFocus(self.includedButtons[0])
				else:
					self.setFocus(self.excludedButtons[0])

			elif self.focusedButtonID == self.buttonOKid:
				self.setFocus(self.buttonClose)
			else:

				if self.excludedButtons[0].isVisible():
					self.setFocus(self.excludedButtons[0])
				else:
					self.setFocus(self.includedButtons[0])

		elif action == self.ACTION_MOVE_LEFT:

			if self.focusedButtonID in self.excludedButtonIDs:
				self.shift = False
				self.setFocus(self.buttonOK)
			elif self.focusedButtonID in self.includedButtonIDs:
				self._getButton(self.focusedButtonID).setLabel(focusedColor="0xFFFFFFFF")

				if self.shift:
					self._updateList("left", False)
				elif self.excludedButtons[0].isVisible():
					self.setFocusId(self.excludedButtonIDs[0])
				else:
					self.setFocus(self.buttonOK)

			elif self.focusedButtonID == self.buttonOKid:

				if self.excludedButtons[0].isVisible():
					self.setFocus(self.excludedButtons[0])
				else:
					self.setFocus(self.includedButtons[0])

			elif self.focusedButtonID == self.buttonCloseID:
				self.setFocusId(self.buttonOKid)
			else:

				if self.excludedButtons[0].isVisible():
					self.setFocus(self.excludedButtons[0])
				else:
					self.setFocus(self.includedButtons[0])

		elif action == self.ACTION_SELECT_ITEM:

			if self.focusedButtonID in self.excludedButtonIDs:
				self.shift = True
				self._updateList("right", True)
			else:
				self.shift = self.shift == False

				if self.focusedButtonID in self.includedButtonIDs:
					button = self._getButton(self.focusedButtonID)

					if self.shift:
						button.setLabel(focusedColor="0xFFFFB70F")
					else:
						button.setLabel(focusedColor="0xFFFFFFFF")

					self.setFocus(button)

		elif action in (self.ACTION_MOUSE_LEFT_CLICK, self.ACTION_MOUSE_DOUBLE_CLICK, self.ACTION_TOUCH_TAP):

			if not self._getButton(self.focusedButtonID).isVisible():
				return
			elif self.focusedButtonID in self.includedButtonIDs:
				self.shift = True
				self._updateList("left", False, setFocus=False)
			elif self.focusedButtonID in self.excludedButtonIDs:
				self.shift = True
				self._updateList("right", True, setFocus=False)

		elif action in (self.ACTION_MOUSE_RIGHT_CLICK, self.ACTION_TOUCH_LONGPRESS):

			if not self._getButton(self.focusedButtonID).isVisible():
				return
			elif self.focusedButtonID in self.includedButtonIDs:
				self.shift = True
				self._updateList("down", False, setFocus=False)

	def onControl(self, control):
		self.focusedButtonID = control.getId()

		if self.focusedButtonID in (self.backgroundID, self.buttonCloseID):
			self.closed = True
			self.close()
		elif self.focusedButtonID == self.buttonOKid:
			self.included.clear()
			[self.included.append(button.getLabel()) for button in self.includedButtons if button.isVisible()]
			self.close()

	def _addAffixButtons(self, items, buttons, x):
		y = self.y + 85

		for _ in range(self.buttonAmount):
			button = self._addControlButton(x, y, self.buttonWidth, self.buttonHeight, alignment=2 + 4)
			button.setVisible(False)
			buttons.append(button)
			y += 30

	def _addBackground(self):
		backgroundFade = self._addControlImage(0, 0, self.viewportWidth, self.viewportHeight, self.blackTexture, colorDiffuse="B3FFFFFF")
		backgroundInvis = self._addControlButton(0, 0, self.viewportWidth, self.viewportHeight, focusTexture="", noFocusTexture="")
		background = self._addControlButton(self.x, self.y, self.windowWidth, self.windowHeight, focusTexture=self.grayTexture, noFocusTexture=self.grayTexture)
		bar = self._addControlButton(
			self.x,
			self.y,
			self.windowWidth,
			40,
			f"[B]{self.title}[/B]",
			focusTexture=self.blueTexture,
			noFocusTexture=self.blueTexture,
			textOffsetX=20,
			shadowColor="0xFF000000",
		)
		excludeBG = self._addControlImage(self.x + 11, self.y + 85, self.buttonWidth, self.buttonHeight * self.buttonAmount, self.dGrayTexture)
		includeBG = self._addControlImage(self.x + self.buttonWidth + 20, self.y + 85, self.buttonWidth, self.buttonHeight * self.buttonAmount, self.dGrayTexture)
		self.addControls([backgroundFade, backgroundInvis, background, bar, includeBG, excludeBG])
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

	def _addLabels(self):
		labelExclude = xbmcgui.ControlLabel(self.x + 10, self.y + 50, 120, 30, f"[COLOR FF0F85A5]{self.settings.getLocalizedString(30103)}[/COLOR]", alignment=2 + 4)
		labelInclude = xbmcgui.ControlLabel(self.x + 140, self.y + 50, 120, 30, f"[COLOR FF0F85A5]{self.settings.getLocalizedString(30104)}[/COLOR]", alignment=2 + 4)
		self.addControls([labelExclude, labelInclude])

	def _calculateViewport(self):
		self.viewportWidth = self.getWidth()
		self.viewportHeight = self.getHeight()
		self.windowWidth = int(406 * self.viewportWidth / 1920)
		self.windowHeight = int(350 * self.viewportHeight / 1080)
		self.x = (self.viewportWidth - self.windowWidth) // 2
		self.y = (self.viewportHeight - self.windowHeight) // 2

	def _createButtons(self):
		self.excludedButtons, self.includedButtons = [], []
		self._addAffixButtons(self.excluded, self.excludedButtons, self.x + 11)
		self._addAffixButtons(self.included, self.includedButtons, self.x + self.buttonWidth + 20)

		for button, label in zip(self.excludedButtons, self.excluded):
			button.setLabel(label)
			button.setVisible(True)

		for button, label in zip(self.includedButtons, self.included):
			button.setLabel(label)
			button.setVisible(True)

		self.buttonOK = self._addControlButton(self.x + 40, self.y + 190, 80, self.buttonHeight, self.settings.getLocalizedString(30066), alignment=2 + 4)
		self.buttonClose = self._addControlButton(self.x + self.buttonWidth + 30, self.y + 190, 80, self.buttonHeight, self.settings.getLocalizedString(30084), alignment=2 + 4)
		self.addControls(self.includedButtons + self.excludedButtons + [self.buttonOK, self.buttonClose])
		self.buttonOKid = self.buttonOK.getId()
		self.buttonCloseID = self.buttonClose.getId()
		self.excludedButtonIDs = [button.getId() for button in self.excludedButtons]
		self.includedButtonIDs = [button.getId() for button in self.includedButtons]
		self.setFocusId(self.excludedButtonIDs[0]) if self.excludedButtons[0].isVisible() else self.setFocusId(self.includedButtonIDs[0])

	def _getButton(self, buttonID):
		return self.getControl(buttonID)

	def _initializePaths(self):
		mediaPath = os.path.join(xbmcaddon.Addon().getAddonInfo("path"), "resources", "media")
		self.blackTexture = os.path.join(mediaPath, "black.png")
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
		[button_.setLabel(button.getLabel()) for button, button_ in zip(buttons, buttonsOutgoing)]

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

	def _updateList(self, direction, excluded, setFocus=True):
		currentTime = time.time()

		if currentTime - self.lastUpdate < 0.05:
			return

		self.lastUpdate = currentTime

		if excluded:
			currentIndex = self.excludedButtonIDs.index(self.focusedButtonID)
			list = self.excludedButtons
		else:
			currentIndex = self.includedButtonIDs.index(self.focusedButtonID)
			list = self.includedButtons

		if direction == "up":
			newIndex = currentIndex - 1
			newButton = next((button for button in list[newIndex::-1] if button.isVisible()))
		elif direction == "down":
			newIndex = currentIndex + 1
			newButton = next((button for button in list[newIndex:] if button.isVisible()), list[0])

		if self.shift:

			if currentIndex == 0 and direction == "up":
				labels = [button.getLabel() for button in list[1:] if button.isVisible()] + [list[0].getLabel()]
				[button.setLabel(labels[index]) for index, button in enumerate(list) if button.isVisible()]
			elif currentIndex == len(list) - 1 and direction == "down":
				labels = [list[-1].getLabel()] + [button.getLabel() for button in list[:-1]]
				[button.setLabel(labels[index]) for index, button in enumerate(list)]
			elif direction == "right" and list == self.excludedButtons:
				self.shift = False
				self._resetShiftableButtons(currentIndex, True)
				currentIndex = currentIndex if self.excludedButtons[currentIndex].isVisible() else currentIndex - 1

				if self.excludedButtons[currentIndex].isVisible():
					newButton = self.excludedButtons[currentIndex]
				else:
					newButton = self.includedButtons[0]

			elif direction == "left" and list == self.includedButtons:
				self.shift = False
				self._resetShiftableButtons(currentIndex, False)
				currentIndex = currentIndex if self.includedButtons[currentIndex].isVisible() else currentIndex - 1

				if self.includedButtons[currentIndex].isVisible():
					newButton = self.includedButtons[currentIndex]
				else:
					newButton = self.excludedButtons[0]

			else:
				currentButton = list[currentIndex]
				currentButtonName = currentButton.getLabel()
				newButtonName = newButton.getLabel()
				currentButton.setLabel(newButtonName)
				newButton.setLabel(currentButtonName)

			if direction in ("up", "down") and setFocus:
				self.includedButtons[currentIndex].setLabel(focusedColor="0xFFFFFFFF")
				newButton.setLabel(focusedColor="0xFFFFB70F")

		if setFocus:
			self.setFocus(newButton)

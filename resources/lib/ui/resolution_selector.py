import os

import xbmcgui
import xbmcaddon


class ResolutionSelector(xbmcgui.WindowDialog):
	ACTION_MOVE_LEFT = 1
	ACTION_MOVE_RIGHT = 2
	ACTION_MOVE_UP = 3
	ACTION_MOVE_DOWN = 4
	ACTION_PREVIOUS_MENU = 10
	ACTION_BACKSPACE = 92

	def __init__(self, *args, **kwargs):
		self.resolutions = kwargs["resolutions"]
		self.closed = False
		self.buttonHeight = 40
		self.buttonAmount = len(self.resolutions)
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
			else:
				self.setFocusId(self.buttonIDs[0])

		elif action == self.ACTION_MOVE_DOWN:

			if self.focusedButtonID in self.buttonIDs:
				self._updateList("down")
			else:
				self.setFocusId(self.buttonIDs[0])

		elif action == self.ACTION_MOVE_RIGHT:

			if self.focusedButtonID not in self.buttonIDs:
				self.setFocusId(self.buttonIDs[0])

		elif action == self.ACTION_MOVE_LEFT:

			if self.focusedButtonID not in self.buttonIDs:
				self.setFocusId(self.buttonIDs[0])

	def onControl(self, control):
		controlID = control.getId()

		if controlID not in self.buttonIDs:
			self.closed = True
		else:
			self.resolution = control.getLabel()

		self.close()

	def _addBackground(self):
		backgroundFade = xbmcgui.ControlImage(0, 0, self.viewportWidth, self.viewportHeight, self.blackTexture, colorDiffuse="CCFFFFFF")
		background = xbmcgui.ControlButton(0, 0, self.viewportWidth, self.viewportHeight, "", focusTexture="", noFocusTexture="")
		self.addControls([backgroundFade, background])

	def _calculateViewport(self):
		self.viewportWidth = self.getWidth()
		self.viewportHeight = self.getHeight()
		self.windowWidth = int(260 * self.viewportWidth / 1920)
		self.windowHeight = int(self.buttonAmount * self.buttonHeight * self.viewportHeight / 1080)
		self.x = (self.viewportWidth - self.windowWidth) // 2
		self.y = (self.viewportHeight - self.windowHeight) // 2

	def _createButtons(self):
		buttons = []
		spacing = 0

		for resolution in self.resolutions:
			buttons.append(
				xbmcgui.ControlButton(
					x=self.x,
					y=self.y + spacing,
					width=self.windowWidth,
					height=self.buttonHeight,
					label=resolution,
					noFocusTexture=self.grayTexture,
					focusTexture=self.focusTexture,
					alignment=2 + 4,
				)
			)
			spacing += self.buttonHeight

		self.addControls(buttons)
		self.buttonIDs = [button.getId() for button in buttons]
		self.setFocusId(self.buttonIDs[0])

	def _getButton(self, buttonID):
		return self.getControl(buttonID)

	def _initializePaths(self):
		mediaPath = os.path.join(xbmcaddon.Addon().getAddonInfo("path"), "resources", "media")
		self.blackTexture = os.path.join(mediaPath, "black.png")
		self.grayTexture = os.path.join(mediaPath, "gray.png")
		self.focusTexture = os.path.join(mediaPath, "focus.png")

	def _updateList(self, direction):
		currentIndex = self.buttonIDs.index(self.focusedButtonID)

		if direction == "up":
			newIndex = currentIndex - 1
		elif direction == "down":
			newIndex = (currentIndex + 1) % self.buttonAmount

		newButton = self._getButton(self.buttonIDs[newIndex])
		self.setFocus(newButton)

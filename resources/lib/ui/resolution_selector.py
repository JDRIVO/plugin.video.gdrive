import os

import xbmcgui
import xbmcaddon


class ResolutionSelector(xbmcgui.WindowDialog):
	ACTION_MOVE_UP = 3
	ACTION_MOVE_DOWN = 4
	ACTION_BACKSPACE = 92

	def __init__(self, *args, **kwargs):
		resolutions = kwargs["resolutions"]
		mediaPath = os.path.join(xbmcaddon.Addon().getAddonInfo("path"), "resources", "media")
		focusTexture = os.path.join(mediaPath, "blue.png")
		noFucusTexture = os.path.join(mediaPath, "gray.png")
		viewportWidth = self.getWidth()
		viewportHeight = self.getHeight()
		windowWidth = int(260 * viewportWidth / 1920)
		buttonWidth = windowWidth
		buttonHeight = 40
		windowHeight = int(len(resolutions) * buttonHeight * viewportHeight / 1080)
		x = int((viewportWidth - windowWidth) / 2)
		x = int((x + windowWidth / 2) - (buttonWidth / 2))
		y = int((viewportHeight - windowHeight) / 2)
		background = xbmcgui.ControlButton(0, 0, viewportWidth, viewportHeight, "", focusTexture="", noFocusTexture="")
		self.addControl(background)
		self.closed = False
		self._createButtons(resolutions, x, y, buttonWidth, buttonHeight, noFucusTexture, focusTexture)

	def onAction(self, action):
		action = action.getId()
		self.buttonId = self.getFocusId()

		if action == self.ACTION_BACKSPACE:
			self.closed = True
			self.close()
		elif action == self.ACTION_MOVE_UP:
			self._updateList("up")
		elif action == self.ACTION_MOVE_DOWN:
			self._updateList("down")

	def onControl(self, control):
		controlId = control.getId()

		if controlId not in self.buttonIds:
			self.closed = True
		else:
			self.resolution = control.getLabel()

		self.close()

	def _createButtons(self, resolutions, x, y, buttonWidth, buttonHeight, noFucusTexture, focusTexture):
		buttons = []
		spacing = 0
		font = "font13"

		for resolution in resolutions:
			buttons.append(
				xbmcgui.ControlButton(
					x=x,
					y=y + spacing,
					width=buttonWidth,
					height=buttonHeight,
					label=resolution,
					font=font,
					noFocusTexture=noFucusTexture,
					focusTexture=focusTexture,
					alignment=2 + 4,
				)
			)
			spacing += buttonHeight

		self.addControls(buttons)
		self.buttonIds = [button.getId() for button in buttons]
		self.setFocusId(self.buttonIds[0])

	def _getButton(self, buttonId):
		return self.getControl(buttonId)

	def _updateList(self, direction):
		currentIndex = self.buttonIds.index(self.buttonId)

		if direction == "up":
			newIndex = currentIndex - 1
		elif direction == "down":
			newIndex = currentIndex + 1

			if newIndex == len(self.buttonIds):
				newIndex = 0

		newButton = self._getButton(self.buttonIds[newIndex])
		self.setFocus(newButton)

"""
Do not delete this file as it is essential for the functionality of this program -
settings need to be imported from this file otherwise strange bugs occur such as
settings not being in sync with settings.xml
"""

import xbmcvfs
import xbmcaddon

from resources.lib.settings import settings

ADDON_PATH = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo("profile"))
SETTINGS = settings.Settings()

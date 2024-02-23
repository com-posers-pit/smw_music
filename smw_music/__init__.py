# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Top level SMW Music Module."""

###############################################################################
# Imports
###############################################################################

from . import exporters, ext_tools, song, spc700, spcmw, ui, utils
from .common import COPYRIGHT_YEAR, RESOURCES, SmwMusicException, __version__

###############################################################################
# API declaration
###############################################################################

__all__ = [
    "__version__",
    "COPYRIGHT_YEAR",
    "RESOURCES",
    "SmwMusicException",
    "exporters",
    "ext_tools",
    "song",
    "spc700",
    "spcmw",
    "ui",
    "utils",
]

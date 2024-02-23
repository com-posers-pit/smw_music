# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

###############################################################################
# Imports
###############################################################################

# Standard library imports
import importlib.resources

###############################################################################
# API variable definitions
###############################################################################

__version__ = "0.3.14"

###############################################################################

COPYRIGHT_YEAR = 2024

###############################################################################

RESOURCES = importlib.resources.files("smw_music.data")

###############################################################################
# API class definitions
###############################################################################


class SmwMusicException(Exception):
    """Parent class for smw_music package Exceptions."""

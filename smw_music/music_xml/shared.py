# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Utilities for handling Music XML conversions."""

###############################################################################
# API constant definitions
###############################################################################

# AMK files are used in windows and need the right line ending.
CRLF = "\r\n"

###############################################################################
# API function definitions
###############################################################################


def notelen_str(notelen: int) -> str:
    rv = f"l{notelen}"
    return rv


###############################################################################
# API class definitions
###############################################################################


class MusicXmlException(Exception):
    """Parent class for MusicXML exceptions."""

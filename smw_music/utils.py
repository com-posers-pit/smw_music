# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Miscellaneous utility functions."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import urllib.error
import urllib.request
from contextlib import suppress

###############################################################################
# API function definitions
###############################################################################


def hexb(val: int) -> str:
    return f"${val:02X}"


###############################################################################


def newest_release() -> tuple[str, str] | None:
    req = urllib.request.Request(
        "https://github.com/com-posers-pit/smw_music/releases/latest"
    )
    with suppress(urllib.error.HTTPError), urllib.request.urlopen(req) as resp:
        url = resp.geturl()
        return (url, url.split("/")[-1].lstrip("v"))
    return None


###############################################################################


def pct(val: float, lim: float = 255) -> str:
    return f"{100*val/lim:3.1f}%"

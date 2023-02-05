# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Miscellaneous utility functions."""

###############################################################################
# API function definitions
###############################################################################


def hexb(val: int) -> str:
    return f"${val:02X}"


###############################################################################


def pct(val: float, lim: float = 255) -> str:
    return f"{100*val/lim:3.1f}%"

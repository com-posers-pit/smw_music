#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""RAM-backed "file system"""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from pathlib import Path

###############################################################################
# API class definitions
###############################################################################


class RamFs:
    _files: dict[tuple[str, ...], bytes | str]

    def __init__(self) -> None:
        self._files = {}

    def insert(self, dst: Path, src: Path) -> None:
        with open(src, "rb") as fobj:
            self.write(dst, fobj.read())

    def read(self, fname: Path) -> str | bytes:
        return self._files[fname.parts]

    def write(self, fname: Path, contents: str | bytes) -> None:
        self._files[fname.parts] = contents

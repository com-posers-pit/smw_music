# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SPCPlayer Interface."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import platform
import subprocess
import threading
from pathlib import Path

###############################################################################
# API function definitions
###############################################################################


def play(player: Path, spc: Path) -> None:
    # Handles linux and OSX, windows is covered on the next line
    args = ["wine", str(player), str(spc)]
    if platform.system() == "Windows":
        args = args[1:]

    threading.Thread(target=subprocess.call, args=(args,)).start()

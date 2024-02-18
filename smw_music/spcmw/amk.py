# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SPCMW-specific logic for interacing with AMK"""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import platform
import subprocess
from pathlib import Path

###############################################################################
# API function calls
###############################################################################


def convert(project_path: Path, timeout: float) -> str:
    match platform.system():
        case "Darwin" | "Linux":
            script = ["sh", "convert.sh"]
        case "Windows":
            script = [str(project_path / "convert.bat")]

    return subprocess.check_output(  # nosec B603
        script, cwd=project_path, stderr=subprocess.STDOUT, timeout=timeout
    ).decode()

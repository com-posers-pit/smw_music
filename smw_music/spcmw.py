# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Music XML -> AMK Converter."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import os
import platform
from contextlib import suppress
from pathlib import Path

# Library imports
import yaml

# Package imports
from smw_music import SmwMusicException

###############################################################################
# Private function definitions
###############################################################################


def _config_dir() -> Path:
    app = "xml2mml"

    sys = platform.system()
    match sys:
        case "Linux":
            default = Path(os.environ["HOME"]) / ".config"
            conf_dir = Path(os.environ.get("XDG_CONFIG_HOME", default))
        case "Windows":
            conf_dir = Path(os.environ["APPDATA"])
        case "Darwin":
            conf_dir = Path(os.environ["HOME"]) / "Library"
        case _:
            raise SmwMusicException(f"Unknown OS {sys}")

    return conf_dir / app


###############################################################################
# API variable definitions
###############################################################################


CONFIG_DIR = _config_dir()
PREFS_FNAME = CONFIG_DIR / "preferences.yaml"
RECENT_PROJECTS_FNAME = CONFIG_DIR / "projects.yaml"

###############################################################################
# API function definitions
###############################################################################


def get_recent_projects() -> list[Path]:
    fname = RECENT_PROJECTS_FNAME
    projects = None
    with suppress(FileNotFoundError):
        with open(fname, "r", encoding="utf8") as fobj:
            projects = yaml.safe_load(fobj)

    if projects is None:
        projects = []

    return [Path(project).resolve() for project in projects]


###############################################################################


def set_recent_projects(projects: list[Path], project_limit: int = 5) -> None:
    if project_limit:
        projects = projects[-project_limit:]

    with open(RECENT_PROJECTS_FNAME, "w", encoding="utf8") as fobj:
        yaml.safe_dump([str(project.resolve()) for project in projects], fobj)


###########################################################################
